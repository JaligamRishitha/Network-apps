# SAP Dialog Styles Updated

## Overview
All dialog components have been updated to match the authentic SAP GUI/Fiori style from the reference image.

## Updated Components

### 1. SAPDialog.tsx
- **Header**: Light blue gradient background (`#b4c7e7` to `#8db3e2`)
- **Border**: 2px solid blue border (`#4f81bd`)
- **Background**: Light blue-gray (`#e8f0f7`)
- **Content Area**: White background with light blue border
- **Buttons**: 
  - OK button: Blue gradient with white text
  - Cancel button: Gray gradient
- **No rounded corners**: Square edges for authentic SAP look

### 2. SAPFormDialog.tsx
- Same styling as SAPDialog
- Multi-field form support
- Input fields with SAP-style borders (`#8db3e2`)
- Validation error messages in red
- Larger dialog size for forms (550px-750px)

### 3. SAPToast.tsx
- **Header**: Colored gradient based on type (success/error/warning/info)
- **Border**: 2px colored border matching message type
- **Background**: Light blue-gray (`#e8f0f7`)
- **Content**: White background with colored border
- **Close button**: SAP-style button with gradient

## Key Style Features

### Colors
- **Header Background**: `linear-gradient(to bottom, #b4c7e7 0%, #8db3e2 100%)`
- **Footer Background**: `linear-gradient(to bottom, #dae8f5 0%, #c5d9f1 100%)`
- **Border Color**: `#4f81bd` (SAP dark blue)
- **Dialog Background**: `#e8f0f7` (SAP light blue-gray)
- **Content Background**: `#ffffff` (white)

### Typography
- **Header Font**: 14px, bold (700), black text with white text-shadow
- **Content Font**: 14px, regular, black text
- **Button Font**: 14px, medium (500) for Cancel, bold (600) for OK

### Buttons
- **OK Button**: 
  - Background: `linear-gradient(to bottom, #5b9bd5 0%, #4472c4 100%)`
  - Border: `1px solid #2e5c8a`
  - Color: White
  - Box shadow for depth
  
- **Cancel Button**:
  - Background: `linear-gradient(to bottom, #f5f5f5 0%, #e0e0e0 100%)`
  - Border: `1px solid #999`
  - Color: Black

### Layout
- **No border radius**: Square corners (borderRadius: 0)
- **Content padding**: White content area with margin inside dialog
- **Shadow**: `0 4px 16px rgba(0, 0, 0, 0.4)` for depth

## Usage in Pages

All pages using dialogs will automatically get the new SAP styling:
- **PM.tsx**: Equipment and work order creation dialogs
- **MM.tsx**: Material creation and management dialogs
- **FI.tsx**: Cost center and approval dialogs
- **SalesQuotation.tsx**: Quotation management dialogs
- **Home.tsx**: Any confirmation dialogs

## Visual Consistency

The dialogs now match the SAP GUI Classic style with:
- Light blue gradient headers
- White content areas with colored borders
- SAP-style buttons with gradients
- Proper shadows and borders
- No rounded corners (authentic SAP look)

This creates a cohesive, professional SAP ERP interface throughout the application.
