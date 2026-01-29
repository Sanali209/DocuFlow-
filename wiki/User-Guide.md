# User Guide

Complete guide to using all features of DocuFlow.

## Table of Contents

1. [Document Management](#document-management)
2. [Task Management](#task-management)
3. [Notes and Journal](#notes-and-journal)
4. [File Attachments](#file-attachments)
5. [OCR Scanning](#ocr-scanning)
6. [Tags and Categories](#tags-and-categories)
7. [Search and Filtering](#search-and-filtering)
8. [Settings](#settings)
9. [Tips and Best Practices](#tips-and-best-practices)

## Document Management

### Creating a New Document

1. Click the **➕ New Document** button in the sidebar
2. Fill in the document information:
   - **Name** (required): The document title
   - **Type**: Select from dropdown (Plan, Mail, Order, Report, Contract, etc.)
   - **Status**: Current state (In Progress, Done, Review, etc.)
   - **Author**: Person responsible for the document
   - **Description**: Brief summary or notes
   - **Registration Date**: Auto-filled with today's date (can be changed)
   - **Done Date**: Completion date (optional, set when status is "Done")
3. Click **Save** to create the document

### Viewing Documents

Documents are displayed as cards in the main view, showing:
- Document name and type badge
- Status indicator with color coding
- Author and dates
- Tags
- Number of tasks and their statuses
- Recent notes (inline)
- Attachment thumbnails

Click on a document name to open the detailed view with full content.

### Editing Documents

1. Click the **Edit** button (pencil icon) on a document card
2. Modify any fields
3. Click **Save** to update

### Deleting Documents

1. Click the **Delete** button (trash icon) on a document card
2. Confirm the deletion
3. The document and all associated tasks, notes, and attachments will be removed

**Note**: This action cannot be undone!

### Document Types

DocuFlow supports various document types:
- **Plan**: Planning documents, roadmaps
- **Mail**: Correspondence, letters
- **Order**: Purchase orders, work orders
- **Report**: Status reports, analysis
- **Contract**: Agreements, contracts
- **Invoice**: Billing documents
- **Other**: Custom types

You can select the type that best fits your document.

### Document Status

Track document progress with status indicators:
- **In Progress**: Currently being worked on (blue)
- **Done**: Completed (green)
- **Review**: Pending review (yellow)
- **Archived**: No longer active (gray)
- **Cancelled**: Cancelled or discarded (red)

## Task Management

### Adding Tasks to Documents

1. Locate the document card
2. In the **Tasks** section, click **+ Add Task**
3. Enter:
   - **Task name**: Description of the task
   - **Status**: Planned, Pending, or Done
   - **Assignee**: Person responsible (optional)
4. Click the checkmark ✓ to save

### Managing Tasks

**Change Task Status**:
- Click on the status badge to cycle through: Planned → Pending → Done

**Update Task Details**:
- Click the edit icon on a task
- Modify name, status, or assignee
- Save changes

**Delete Tasks**:
- Click the delete icon (🗑️) on a task
- Confirm deletion

**Reorder Tasks**:
- Tasks are displayed in the order they were created
- Future: Drag-and-drop reordering

### Task Status Meanings

- **Planned** (📋 gray): Task is scheduled but not started
- **Pending** (⏳ yellow): Task is in progress
- **Done** (✓ green): Task is completed

### Assignee Management

Assign tasks to team members:
1. Select or type an assignee name when creating/editing a task
2. The assignee dropdown shows previously used names for quick selection
3. Filter tasks by assignee using the filter panel

## Notes and Journal

### Adding Notes

1. Click **Add Note** (📝) on a document card
2. Enter your note text in the dialog
3. Click **Add** to save

Notes are displayed inline in the document card with:
- Timestamp
- Note content
- Attachments (if any)

### Use Cases for Notes

- **Activity Log**: Record actions taken on the document
- **Status Updates**: Note progress or changes
- **Communication**: Log conversations or decisions
- **Reminders**: Add follow-up items or important dates

## File Attachments

### Uploading Files

1. Click **Add Attachment** (📎) on a document card
2. Select one or more files from your computer
3. Supported formats: PDF, JPEG, PNG, JPG
4. Files are uploaded and thumbnails displayed

### Viewing Attachments

- **Images**: Click thumbnail to open full-screen preview
- **PDFs**: Click to download and view in your PDF reader
- **Gallery View**: Navigate between multiple images in preview mode

### Managing Attachments

- **Delete**: Click the X icon on a thumbnail to remove
- **Download**: Click the download icon to save locally
- **Scan Integration**: Scanned documents are automatically saved as attachments

## OCR Scanning

### Scanning Documents

DocuFlow can extract text and tables from images and PDFs using AI-powered OCR.

1. Click **➕ New Document** or edit an existing document
2. Scroll to the **OCR Scanning** section
3. Click **Select Files to Scan**
4. Choose one or more files (images or PDFs)
5. Click **Scan** to start processing

### What Happens During Scanning

1. Files are uploaded to the OCR service
2. Text and tables are extracted using IBM Docling
3. Document name is auto-extracted (if configured)
4. Extracted content is formatted as Markdown
5. Content is appended to the document's content field
6. Files are automatically saved as attachments

### Multi-File Scanning

You can scan multiple files in one operation:
- Select multiple files at once
- Content is processed sequentially
- Each file's content is appended in order
- Useful for multi-page documents split across files

### Extracted Content Features

- **Text Recognition**: Accurate OCR for printed text
- **Table Preservation**: Tables maintained in markdown format
- **Headers**: Section headers detected and formatted
- **Paragraphs**: Text organized into paragraphs
- **Lists**: Bullet points and numbered lists recognized

### Viewing Extracted Content

- Content is displayed in the **Content** field of the document
- Markdown formatting is applied
- Tables are rendered with proper alignment
- View in read-only mode by clicking the document name

### OCR Service Configuration

1. Click **Settings** (⚙️) in the sidebar
2. Configure:
   - **OCR Service URL**: Your OCR endpoint (local or hosted)
   - **Document Name Regex**: Pattern to extract document names
3. Click **Save**

**Default Regex**: `(?si)Order:\s*(.*?)\s*Date:`
- Extracts text between "Order:" and "Date:"
- Case-insensitive, multiline
- Customize for your document format

## Tags and Categories

### Adding Tags

1. When creating or editing a document
2. In the **Tags** field, start typing
3. Select from existing tags or create new ones
4. Add multiple tags to a document

### Tag Autocomplete

- As you type, matching tags appear
- Press Enter or click to select
- Tags are shared across all documents
- Helps maintain consistent categorization

### Tag Examples

Common tagging strategies:
- **Priority**: `urgent`, `high-priority`, `low-priority`
- **Category**: `financial`, `legal`, `technical`, `hr`
- **Project**: `project-alpha`, `q1-2024`, `client-acme`
- **Status**: `needs-review`, `approved`, `draft`
- **Department**: `engineering`, `sales`, `marketing`

### Managing Tags

- **View All Tags**: Use the filter panel to see all available tags
- **Consistent Naming**: Use autocomplete to avoid duplicates
- **Bulk Filtering**: Filter by multiple tags simultaneously

## Search and Filtering

### Quick Search

Use the search bar at the top to search across:
- Document names
- Descriptions
- OCR-extracted content
- Task names

Just start typing, and results update in real-time.

### Advanced Filtering

Click the **Filter** button to access multi-criteria filtering:

#### Filter Options

**Type Filter**:
- Select one or more document types
- Show only documents of selected types

**Status Filter**:
- Filter by document status
- Multiple selections allowed

**Tag Filter**:
- Filter by one or more tags
- Documents must have at least one selected tag

**Date Filters**:
- **Registration Date Range**: When document was created
- **Done Date Range**: When document was completed
- Use date pickers or type dates

**Task Filters**:
- **Task Status**: Show documents with specific task statuses
  - Example: Show all documents with "Pending" tasks
- **Assignee**: Filter documents by who tasks are assigned to

**Sort Options**:
- Registration Date (newest/oldest)
- Name (A-Z, Z-A)
- Status
- Type

### Filter Presets

Save commonly-used filter combinations:

**Creating a Preset**:
1. Configure your filters
2. Click **Save as Preset**
3. Enter a name (e.g., "Urgent Pending Tasks")
4. Click **Save**

**Using Presets**:
1. Click **Presets** dropdown
2. Select a saved preset
3. Filters are applied instantly

**Managing Presets**:
- **Load**: Click preset name to apply
- **Delete**: Click X next to preset to remove
- **Update**: Currently requires deleting and recreating

### Search Tips

- **Partial Match**: Search finds partial word matches
- **Case Insensitive**: Search is not case-sensitive
- **Multiple Terms**: Space-separated terms search for all
- **Clear Filters**: Click "Clear All" to reset filters

## Settings

### Accessing Settings

Click the **⚙️ Settings** icon in the sidebar.

### OCR Service URL

Configure where OCR requests are sent:
- **Local**: `http://localhost:7860` (if running locally)
- **Hosted**: URL of your deployed OCR service (e.g., Hugging Face Space)
- **Format**: Must include protocol (`http://` or `https://`)

**To change**:
1. Enter new URL
2. Click **Save**
3. Test by scanning a document

### Document Name Regex

Configure the pattern used to extract document names from OCR content:

**Default**: `(?si)Order:\s*(.*?)\s*Date:`

**Components**:
- `(?si)`: Case-insensitive, multiline flags
- `Order:`: Start marker
- `\s*`: Optional whitespace
- `(.*?)`: Captured group (the document name)
- `\s*Date:`: End marker

**Custom Examples**:
```regex
# Extract from "Invoice: XYZ123 Date:"
(?si)Invoice:\s*(.*?)\s*Date:

# Extract from "Document Name: [name]"
(?si)Document Name:\s*\[(.*?)\]

# Extract first line
^(.*)$
```

**Testing Your Regex**:
1. Update the pattern
2. Click **Save**
3. Scan a test document
4. Check if name is extracted correctly

## Tips and Best Practices

### Organization Strategies

**Consistent Naming**:
- Use clear, descriptive document names
- Include dates or identifiers: "Project Plan Q1 2024"
- Avoid generic names like "Document 1"

**Tagging System**:
- Establish tag conventions for your team
- Use hierarchical tags: `project:alpha`, `project:beta`
- Limit to 3-5 tags per document for clarity

**Document Types**:
- Use types consistently across similar documents
- Create custom types if needed (select "Other" and add description)

### Task Management

**Status Workflow**:
1. Create tasks as **Planned** during planning phase
2. Move to **Pending** when work begins
3. Mark **Done** when completed
4. Review "Done Date" of document when all tasks complete

**Assignment Best Practices**:
- Assign one person per task for clear ownership
- Use full names for clarity
- Review assignee filter regularly to balance workload

### OCR Optimization

**Best Scan Quality**:
- Use clear, high-resolution images (300 DPI or higher)
- Ensure good lighting and contrast
- Scan pages flat to avoid distortion
- PDFs generally give better results than images

**Multi-Page Documents**:
- Scan all pages at once for continuous content
- Or scan individually and content appends in order
- Check extracted content for completeness

**Post-Scan Review**:
- Always review extracted content for accuracy
- OCR may misread handwriting or poor-quality scans
- Edit content field directly if corrections needed

### Search Efficiency

**Use Presets**:
- Create presets for frequent searches
- Examples: "My Tasks", "Urgent Items", "This Week's Docs"

**Combine Filters**:
- Use multiple criteria for precise results
- Example: Type=Order + Status=Pending + Tag=urgent

**Regular Review**:
- Set up preset for "Documents needing review"
- Filter by old registration dates periodically

### Performance

**Large Databases**:
- If performance degrades with many documents, consider:
  - Archiving old documents
  - Migrating to PostgreSQL
  - Deploying on more powerful hardware

**File Sizes**:
- Keep attachments reasonably sized
- Compress large PDFs before uploading
- OCR works best on files under 10MB

### Mobile Usage

DocuFlow is optimized for mobile:
- **Compact View**: Cards adapt to smaller screens
- **Touch Targets**: Buttons sized for fingers
- **Icon Navigation**: Sidebar shows icons only on mobile
- **Responsive Tables**: Scroll horizontally for markdown tables

**Mobile Tips**:
- Use search and filters to find documents quickly
- Tap once to view, tap and hold for options
- Rotate to landscape for better table viewing

## Keyboard Shortcuts

Coming in a future release:
- `Ctrl/Cmd + N`: New document
- `Ctrl/Cmd + F`: Focus search
- `Ctrl/Cmd + S`: Save (in form)
- `Esc`: Close modals

## Need Help?

- Check [FAQ & Troubleshooting](FAQ-and-Troubleshooting.md) for common issues
- Review [API Documentation](API-Documentation.md) for programmatic access
- See [Getting Started](Getting-Started.md) for setup issues
- Report bugs on [GitHub Issues](https://github.com/Sanali209/DocuFlow-/issues)

---

[← Back to Getting Started](Getting-Started.md) | [Next: API Documentation →](API-Documentation.md)
