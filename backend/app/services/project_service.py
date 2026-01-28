from typing import List, Optional
import sys
import os
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Project, ProjectFile
from app.schemas import ProjectCreate, ProjectFileCreate, ProjectUpdate
from app.services.filesystem_service import FileSystemService

# Simple inline debug logger
def debug_log(message):
    """Write debug message to both stdout and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"

    # Write to file
    log_file = os.path.join(os.path.dirname(__file__), '..', '..', 'visual_editor.log')
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(full_message + '\n')
    except Exception as e:
        print(f"Log file error: {e}")

    # Write to stdout
    print(full_message)


class ProjectService:
    """Service for managing projects"""

    @staticmethod
    def create_project(db: Session, project: ProjectCreate, owner_id: int) -> Project:
        """Create a new project"""

        db_project = Project(
            **project.model_dump(),
            owner_id=owner_id,
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        # Create initial project structure (both DB and filesystem)
        ProjectService._create_initial_files(db, db_project.id, db_project.name, project.template)

        return db_project

    @staticmethod
    def get_project(db: Session, project_id: int, owner_id: int) -> Optional[Project]:
        """Get a project by ID"""

        project = db.query(Project).filter(Project.id == project_id, Project.owner_id == owner_id).first()

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        return project

    @staticmethod
    def get_projects(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects for a user"""
        # Query with ordering - noload is already set at model level
        return (
            db.query(Project)
            .filter(Project.owner_id == owner_id)
            .order_by(Project.updated_at.desc())  # Most recently updated first
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_project(db: Session, project_id: int, owner_id: int, project_update: ProjectUpdate) -> Project:
        """Update a project"""

        project = ProjectService.get_project(db, project_id, owner_id)

        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: int, owner_id: int) -> bool:
        """Delete a project"""

        project = ProjectService.get_project(db, project_id, owner_id)

        # Delete physical files
        FileSystemService.delete_project(project_id)

        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def get_project_files(db: Session, project_id: int, owner_id: int) -> List[dict]:
        """Get all files for a project from filesystem"""

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        # Get file metadata from database
        db_files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()

        # Read content from filesystem
        files_with_content = []
        for db_file in db_files:
            content = FileSystemService.read_file(project_id, db_file.filepath)
            files_with_content.append(
                {
                    "id": db_file.id,
                    "project_id": db_file.project_id,
                    "filename": db_file.filename,
                    "filepath": db_file.filepath,
                    "content": content or "",
                    "language": db_file.language,
                    "created_at": db_file.created_at,
                    "updated_at": db_file.updated_at,
                }
            )

        return files_with_content

    @staticmethod
    def add_file_to_project(db: Session, project_id: int, owner_id: int, file_data: ProjectFileCreate) -> dict:
        """Add a file to a project"""
        from app.services.git_service import GitService

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        # Extract content from file_data
        content = file_data.content if hasattr(file_data, "content") else ""

        # Create file metadata in database (without content)
        file_dict = file_data.model_dump()
        file_dict.pop("content", None)  # Remove content if present

        db_file = ProjectFile(**file_dict)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # Write to filesystem
        FileSystemService.write_file(project_id, db_file.filepath, content)

        # Commit to Git
        GitService.commit_changes(project_id, f"Add file: {db_file.filepath}", [db_file.filepath])

        return {
            "id": db_file.id,
            "project_id": db_file.project_id,
            "filename": db_file.filename,
            "filepath": db_file.filepath,
            "content": content,
            "language": db_file.language,
            "created_at": db_file.created_at,
            "updated_at": db_file.updated_at,
        }

    @staticmethod
    def update_file(db: Session, file_id: int, project_id: int, owner_id: int, content: str) -> dict:
        """Update a file's content"""
        from app.services.git_service import GitService

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        file = db.query(ProjectFile).filter(ProjectFile.id == file_id, ProjectFile.project_id == project_id).first()

        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        # Update filesystem
        FileSystemService.write_file(project_id, file.filepath, content)

        # Commit to Git
        GitService.commit_changes(project_id, f"Update file: {file.filepath}", [file.filepath])

        # Update timestamp in database
        from datetime import datetime

        file.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(file)

        return {
            "id": file.id,
            "project_id": file.project_id,
            "filename": file.filename,
            "filepath": file.filepath,
            "content": content,
            "language": file.language,
            "created_at": file.created_at,
            "updated_at": file.updated_at,
        }

    @staticmethod
    def delete_file(db: Session, file_id: int, project_id: int, owner_id: int) -> bool:
        """Delete a file from a project"""
        from app.services.git_service import GitService

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        file = db.query(ProjectFile).filter(ProjectFile.id == file_id, ProjectFile.project_id == project_id).first()

        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        filepath = file.filepath

        # Delete from filesystem
        FileSystemService.delete_file(project_id, filepath)

        # Delete from database
        db.delete(file)
        db.commit()

        # Commit deletion to Git
        GitService.commit_changes(project_id, f"Delete file: {filepath}")

        return True

    @staticmethod
    def apply_visual_edits(
        db: Session, project_id: int, owner_id: int, filepath: str, element_selector: str,
        style_changes: dict = None, class_name: str = None
    ) -> dict:
        """
        Apply visual style changes and/or className changes directly to a component file.

        Args:
            db: Database session
            project_id: Project ID
            owner_id: User ID
            filepath: Path to the file to edit (e.g., 'src/components/Button.tsx')
            element_selector: CSS-like selector or element tag name
            style_changes: (Optional) Dict of style properties to apply (e.g., {'color': '#fff', 'backgroundColor': '#000'})
            class_name: (Optional) New className string to replace the existing one

        Returns:
            Dict with success status and updated file info
        """

        from app.services.git_service import GitService

        print(f"\n[SERVICE] ========== APPLY VISUAL EDITS ==========")
        print(f"[SERVICE] Project ID: {project_id}")
        print(f"[SERVICE] Filepath: {filepath}")
        print(f"[SERVICE] Element selector: {element_selector}")
        print(f"[SERVICE] Style changes: {style_changes}")
        print(f"[SERVICE] Class name: {class_name}")

        # Verify ownership
        ProjectService.get_project(db, project_id, owner_id)

        # Read current file content
        content = FileSystemService.read_file(project_id, filepath)
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {filepath}")

        print(f"[SERVICE] File read successfully, length: {len(content)} characters")

        modified_content = content
        changes_applied = {}

        # Get original className from edit_data if available
        original_class_name = None
        if hasattr(ProjectService, 'current_edit_data'):
            original_class_name = getattr(ProjectService, 'current_edit_data', {}).get('original_class_name')
            print(f"[SERVICE] Original class name: {original_class_name}")

        # Apply style changes if provided
        if style_changes:
            print(f"[SERVICE] Applying style changes...")
            modified_content = ProjectService._apply_styles_to_jsx(
                modified_content, element_selector, style_changes, original_class_name
            )
            changes_applied['styles'] = style_changes

        # Apply className changes if provided
        if class_name is not None:
            print(f"[SERVICE] Applying className changes...")
            modified_content = ProjectService._apply_classname_to_jsx(
                modified_content, element_selector, class_name, original_class_name
            )
            changes_applied['className'] = class_name

        if modified_content == content:
            # No changes made
            return {
                "success": False,
                "message": "No matching element found or changes already applied",
                "filepath": filepath,
            }

        # Write modified content back to filesystem
        FileSystemService.write_file(project_id, filepath, modified_content)

        # Commit to Git
        commit_msg = f"Visual edit: Apply changes to {element_selector} in {filepath}"
        GitService.commit_changes(project_id, commit_msg, [filepath])

        return {
            "success": True,
            "message": f"Applied visual edits to {filepath}",
            "filepath": filepath,
            "changes_applied": changes_applied,
            "modified_content": modified_content,  # Include for HMR file push
        }

    @staticmethod
    def _apply_styles_to_jsx(content: str, element_selector: str, style_changes: dict, original_class_name: str = None) -> str:
        """
        Apply style changes to JSX/TSX content.
        Supports selectors: tagname, tagname.classname, tagname#id, nth-child, nth-of-type, and complex selectors

        Args:
            content: File content
            element_selector: Element selector (e.g., 'button', 'div.container', 'Button#main',
                            'div:nth-child(2)', 'div:nth-of-type(2)', 'div.container > button:nth-of-type(2)')
            style_changes: Dict of CSS properties to apply
            original_class_name: Original className to match (for more specificity)

        Returns:
            Modified content with styles applied
        """
        import re

        # Convert CSS property names to camelCase for React inline styles
        def to_camel_case(prop):
            """Convert CSS property to camelCase (e.g., background-color -> backgroundColor)"""
            parts = prop.split("-")
            return parts[0] + "".join(word.capitalize() for word in parts[1:])

        react_styles = {to_camel_case(k): v for k, v in style_changes.items()}

        # Parse selector - extract the last element in the selector chain
        # For complex selectors like "div.container > button:nth-child(2)",
        # we want to target "button:nth-child(2)"
        debug_log("=" * 60)
        debug_log("[SERVICE] APPLY STYLES")
        debug_log(f"[SERVICE] Original selector: {element_selector}")
        debug_log(f"[SERVICE] Original class name: {original_class_name}")

        selector_parts = element_selector.split()
        if len(selector_parts) > 1:
            # Take the last part (the actual target element)
            element_selector = selector_parts[-1]
            debug_log(f"[SERVICE] Extracted target element: {element_selector}")

        # Parse selector to extract tag name, class, id, and nth-child/nth-of-type
        tag_name = element_selector
        class_filter = None
        id_filter = None
        nth_child = None

        # Extract nth-child or nth-of-type if present (treat them the same)
        nth_match = re.search(r':nth-(?:child|of-type)\((\d+)\)', element_selector)
        if nth_match:
            nth_child = int(nth_match.group(1))
            element_selector = element_selector[:nth_match.start()]  # Remove :nth-child/:nth-of-type from selector
            debug_log(f"[SERVICE] Found nth position: {nth_child}")

        if '.' in element_selector:
            tag_name, class_filter = element_selector.split('.', 1)
            debug_log(f"[SERVICE] Tag: {tag_name}, Class filter: {class_filter}")
        elif '#' in element_selector:
            tag_name, id_filter = element_selector.split('#', 1)
            debug_log(f"[SERVICE] Tag: {tag_name}, ID filter: {id_filter}")
        else:
            tag_name = element_selector
            debug_log(f"[SERVICE] Tag: {tag_name} (no class/id filter)")

        # IMPORTANT: If we have original_class_name and nth_child,
        # prioritize filtering by className FIRST, then selecting nth element from that filtered set
        # This is more accurate than searching globally for nth-of-type

        # Pattern to find JSX opening tag with the given element name
        tag_pattern = rf"<{tag_name}(?:\s+[^>]*?)?"

        # Find all occurrences and filter by className, id, and nth-child
        matches = list(re.finditer(tag_pattern, content))
        debug_log(f"[SERVICE] Found {len(matches)} total matches for tag '{tag_name}'")

        # Build list of candidate matches
        # Strategy: If original_class_name exists, use it as PRIMARY filter
        # Then apply nth-child to that filtered set (not globally)
        candidates = []
        use_original_class = original_class_name and not class_filter and not id_filter

        for match in matches:
            tag_start = match.start()
            # Find where this tag ends (> or />)
            tag_end_match = re.search(r"(?:>|/>)", content[tag_start:])
            if not tag_end_match:
                continue

            tag_full_end = tag_start + tag_end_match.end()
            tag_content = content[tag_start:tag_full_end]

            # Check if this match has the required className or id
            match_passes = False

            if class_filter:
                # Look for className attribute containing the filter
                class_match = re.search(r'className=(?:"([^"]*)"|{`([^`]*)`}|{\'([^\']*)\'})', tag_content)
                if class_match:
                    class_value = class_match.group(1) or class_match.group(2) or class_match.group(3)
                    if class_filter in class_value.split():
                        match_passes = True
            elif id_filter:
                # Look for id attribute
                id_match = re.search(rf'id=(?:"{id_filter}"|{{\'{id_filter}\'}})', tag_content)
                if id_match:
                    match_passes = True
            elif use_original_class:
                # PRIORITY: Use original className as primary filter
                # This is more reliable than global nth-of-type matching
                class_match = re.search(r'className=(?:"([^"]*)"|{`([^`]*)`}|{\'([^\']*)\'})', tag_content)
                if class_match:
                    class_value = class_match.group(1) or class_match.group(2) or class_match.group(3)
                    # Match if the className is exactly the same
                    if class_value == original_class_name:
                        match_passes = True
                        debug_log(f"[SERVICE] Found element with matching className: {class_value[:50]}...")
            else:
                # No filter, all matches are candidates
                match_passes = True

            if match_passes:
                candidates.append((match, tag_start, tag_full_end, tag_content))

        debug_log(f"[SERVICE] Found {len(candidates)} candidate matches after filtering")

        # If nth-child is specified, use it to select the right match
        target_match = None
        if nth_child is not None and len(candidates) >= nth_child:
            target_match = candidates[nth_child - 1]  # nth-child is 1-indexed
            debug_log(f"[SERVICE] Selected match #{nth_child} from {len(candidates)} candidates")
        elif len(candidates) > 0:
            target_match = candidates[0]  # Use first match if no nth-child
            debug_log(f"[SERVICE] Using first match (no nth-child specified)")

        if not target_match:
            debug_log(f"[SERVICE] ERROR: No target match found! Selector: {element_selector}, OriginalClass: {original_class_name}")
            return content

        _, tag_start, tag_full_end, tag_content = target_match
        debug_log(f"[SERVICE] Target element: {tag_content[:100]}...")
        debug_log(f"[SERVICE] Applying styles: {react_styles}")

        # Check if there's already a style attribute
        existing_style_match = re.search(r'style=\{\{([^}]*)\}\}', tag_content)

        if existing_style_match:
            # Extract existing style properties
            existing_style_str = existing_style_match.group(1).strip()

            # Parse existing styles into a dict
            existing_styles = {}
            if existing_style_str:
                # Split by comma, handling quoted values
                style_pairs = re.findall(r"(\w+):\s*'([^']*)'", existing_style_str)
                for prop, val in style_pairs:
                    existing_styles[prop] = val

            # Merge new styles (new styles override existing ones)
            existing_styles.update(react_styles)

            # Build new style string
            new_style_string = ", ".join([f"{k}: '{v}'" for k, v in existing_styles.items()])
            new_style_attr = f"style={{{{{new_style_string}}}}}"

            # Replace the old style attribute with the new one
            new_tag_content = re.sub(r'style=\{\{[^}]*\}\}', new_style_attr, tag_content)
        else:
            # No existing style attribute - add it
            # Build style string
            style_string = ", ".join([f"{k}: '{v}'" for k, v in react_styles.items()])
            new_style_attr = f" style={{{{{style_string}}}}}"

            # Find a good place to insert it - right after the tag name
            # Insert after the tag name and any whitespace
            insert_pos = len(f"<{tag_name}")
            new_tag_content = tag_content[:insert_pos] + new_style_attr + tag_content[insert_pos:]

        # Replace the original tag with the modified one
        modified_content = content[:tag_start] + new_tag_content + content[tag_full_end:]

        return modified_content

    @staticmethod
    def _apply_classname_to_jsx(content: str, element_selector: str, class_name: str, original_class_name: str = None) -> str:
        """
        Apply className changes to JSX/TSX content.
        Supports selectors: tagname, tagname.classname, tagname#id, nth-child, nth-of-type, and complex selectors

        Args:
            content: File content
            element_selector: Element selector (e.g., 'button', 'div.container', 'Button#main',
                            'div:nth-child(2)', 'div:nth-of-type(2)', 'div.container > button:nth-of-type(2)')
            class_name: New className string
            original_class_name: Original className to match (for more specificity)

        Returns:
            Modified content with className applied
        """
        import re

        # Parse selector - extract the last element in the selector chain
        print(f"[DEBUG] [ClassName] Original selector: {element_selector}")
        print(f"[DEBUG] [ClassName] Original class name: {original_class_name}")

        selector_parts = element_selector.split()
        if len(selector_parts) > 1:
            element_selector = selector_parts[-1]
            print(f"[DEBUG] [ClassName] Extracted target element: {element_selector}")

        # Parse selector to extract tag name, class, id, and nth-child/nth-of-type
        tag_name = element_selector
        class_filter = None
        id_filter = None
        nth_child = None

        # Extract nth-child or nth-of-type if present
        nth_match = re.search(r':nth-(?:child|of-type)\((\d+)\)', element_selector)
        if nth_match:
            nth_child = int(nth_match.group(1))
            element_selector = element_selector[:nth_match.start()]
            print(f"[DEBUG] [ClassName] Found nth position: {nth_child}")

        if '.' in element_selector:
            tag_name, class_filter = element_selector.split('.', 1)
            print(f"[DEBUG] [ClassName] Tag: {tag_name}, Class filter: {class_filter}")
        elif '#' in element_selector:
            tag_name, id_filter = element_selector.split('#', 1)
            print(f"[DEBUG] [ClassName] Tag: {tag_name}, ID filter: {id_filter}")
        else:
            tag_name = element_selector
            print(f"[DEBUG] [ClassName] Tag: {tag_name} (no class/id filter)")

        # IMPORTANT: If we have original_class_name and nth_child,
        # prioritize filtering by className FIRST, then selecting nth element from that filtered set
        # This is more accurate than searching globally for nth-of-type

        # Pattern to find JSX opening tag with the given element name
        tag_pattern = rf"<{tag_name}(?:\s+[^>]*?)?"

        # Find all occurrences and filter by className, id, and nth-child
        matches = list(re.finditer(tag_pattern, content))
        print(f"[DEBUG] [ClassName] Found {len(matches)} total matches for tag '{tag_name}'")

        # Build list of candidate matches
        # Strategy: If original_class_name exists, use it as PRIMARY filter
        # Then apply nth-child to that filtered set (not globally)
        candidates = []
        use_original_class = original_class_name and not class_filter and not id_filter

        for match in matches:
            tag_start = match.start()
            # Find where this tag ends (> or />)
            tag_end_match = re.search(r"(?:>|/>)", content[tag_start:])
            if not tag_end_match:
                continue

            tag_full_end = tag_start + tag_end_match.end()
            tag_content = content[tag_start:tag_full_end]

            # Check if this match has the required className or id
            match_passes = False

            if class_filter:
                # Look for className attribute containing the filter
                class_match = re.search(r'className=(?:"([^"]*)"|{`([^`]*)`}|{\'([^\']*)\'})', tag_content)
                if class_match:
                    class_value = class_match.group(1) or class_match.group(2) or class_match.group(3)
                    if class_filter in class_value.split():
                        match_passes = True
            elif id_filter:
                # Look for id attribute
                id_match = re.search(rf'id=(?:"{id_filter}"|{{\'{id_filter}\'}})', tag_content)
                if id_match:
                    match_passes = True
            elif use_original_class:
                # PRIORITY: Use original className as primary filter
                # This is more reliable than global nth-of-type matching
                class_match = re.search(r'className=(?:"([^"]*)"|{`([^`]*)`}|{\'([^\']*)\'})', tag_content)
                if class_match:
                    class_value = class_match.group(1) or class_match.group(2) or class_match.group(3)
                    # Match if the className is exactly the same
                    if class_value == original_class_name:
                        match_passes = True
                        print(f"[DEBUG] [ClassName] Found element with matching className: {class_value[:50]}...")
            else:
                # No filter, all matches are candidates
                match_passes = True

            if match_passes:
                candidates.append((match, tag_start, tag_full_end, tag_content))

        print(f"[DEBUG] [ClassName] Found {len(candidates)} candidate matches after filtering")

        # If nth-child is specified, use it to select the right match
        target_match = None
        if nth_child is not None and len(candidates) >= nth_child:
            target_match = candidates[nth_child - 1]  # nth-child is 1-indexed
            print(f"[DEBUG] Selected match #{nth_child} from {len(candidates)} candidates")
        elif len(candidates) > 0:
            target_match = candidates[0]  # Use first match if no nth-child
            print(f"[DEBUG] Using first match (no nth-child specified)")

        if not target_match:
            print(f"[DEBUG] [ClassName] No target match found!")
            return content

        _, tag_start, tag_full_end, tag_content = target_match
        print(f"[DEBUG] [ClassName] Target element: {tag_content[:100]}...")
        print(f"[DEBUG] [ClassName] Applying className: {class_name}")

        # Check if there's already a className attribute
        # Matches: className="..." or className='...' or className={...}
        existing_classname_match = re.search(r'className=(?:"([^"]*)"|\'([^\']*)\'|\{([^}]*)\})', tag_content)

        if existing_classname_match:
            # Replace the existing className attribute
            new_classname_attr = f'className="{class_name}"'
            new_tag_content = re.sub(
                r'className=(?:"[^"]*"|\'[^\']*\'|\{[^}]*\})',
                new_classname_attr,
                tag_content
            )
        else:
            # No existing className attribute - add it
            new_classname_attr = f' className="{class_name}"'

            # Insert after the tag name and any whitespace
            insert_pos = len(f"<{element_selector}")
            new_tag_content = tag_content[:insert_pos] + new_classname_attr + tag_content[insert_pos:]

        # Replace the original tag with the modified one
        modified_content = content[:tag_start] + new_tag_content + content[tag_full_end:]

        return modified_content

    @staticmethod
    def _create_initial_files(db: Session, project_id: int, project_name: str, template: str):
        """Create initial project structure based on template"""

        # Create physical project structure (includes Git init)
        FileSystemService.create_project_structure(project_id, project_name)

        if template == "react-vite":
            # Only store metadata in database (content is in filesystem)
            initial_files = [
                {
                    "project_id": project_id,
                    "filename": "App.tsx",
                    "filepath": "src/App.tsx",
                    "language": "tsx",
                },
                {
                    "project_id": project_id,
                    "filename": "main.tsx",
                    "filepath": "src/main.tsx",
                    "language": "tsx",
                },
                {
                    "project_id": project_id,
                    "filename": "index.css",
                    "filepath": "src/index.css",
                    "language": "css",
                },
                {
                    "project_id": project_id,
                    "filename": "tsconfig.node.json",
                    "filepath": "tsconfig.node.json",
                    "language": "json",
                },
            ]

            for file_data in initial_files:
                db_file = ProjectFile(**file_data)
                db.add(db_file)

            db.commit()
