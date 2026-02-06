# SAP ERP UI Style Guide

This application now features an authentic SAP Fiori/SAP GUI-inspired interface design.

## Design Features

### 1. SAP Shell Navigation
- **Dark blue sidebar** (#354a5f) with hierarchical navigation
- **Expandable menu items** for module organization
- **Active state indicators** with blue accent (#0a6ed1)
- **User profile section** in footer with sign-out functionality

### 2. SAP GUI Classic Elements
- **Section headers** with gradient blue background
- **Tab navigation** with classic SAP styling
- **Tree navigation** for hierarchical data
- **Toolbar buttons** with icons and hover states
- **Status indicators** (success, warning, error, info)

### 3. Color Palette
```css
SAP Shell: #354a5f (dark blue)
SAP Accent: #0a6ed1 (bright blue)
SAP GUI Blue: #c5d9f1 (light blue)
Success: #107e3e (green)
Warning: #e9730c (orange)
Error: #bb0000 (red)
Info: #0a6ed1 (blue)
```

### 4. Available CSS Classes

#### Containers
- `.sap-gui-container` - Main container with SAP GUI styling
- `.sap-gui-section` - Section header with gradient
- `.sap-gui-panel` - White panel with border
- `.sap-fiori-card` - Modern Fiori card style

#### Navigation
- `.sap-gui-tabs` - Tab container
- `.sap-gui-tab` - Individual tab (add `.active` for selected)
- `.sap-tree` - Tree navigation container
- `.sap-tree-item` - Tree item (add `.selected` for active)

#### Toolbar
- `.sap-toolbar` - Toolbar container
- `.sap-toolbar-button` - Standard button
- `.sap-toolbar-button.primary` - Primary action button

#### Forms
- `.sap-form-group` - Form field container
- `.sap-form-label` - Field label
- `.sap-form-input` - Input field

#### Tables
- `.sap-table` - SAP-styled data table
- Includes hover and selection states

#### Status Badges
- `.sap-status` - Base status badge
- `.sap-status.success` - Green success badge
- `.sap-status.warning` - Orange warning badge
- `.sap-status.error` - Red error badge
- `.sap-status.info` - Blue info badge

#### Layout Utilities
- `.sap-grid` - Grid container
- `.sap-grid-2`, `.sap-grid-3`, `.sap-grid-4` - 2, 3, or 4 column grids
- `.sap-flex` - Flex container with gap
- `.sap-flex-between` - Flex with space-between

## Module Pages

### Plant Maintenance (PM)
- Equipment master data table
- Work order management with KPIs
- Maintenance schedule view
- History tracking
- Tree navigation for different views

### Materials Management (MM)
- Material master data with search
- Purchase order processing
- Inventory overview with metrics
- Vendor management
- Multi-tab interface

### Financial Accounting (FI)
- Approvals inbox with action buttons
- Cost center overview with budget tracking
- General ledger accounts
- Financial reports dashboard
- Real-time budget utilization

## Dashboard
- KPI cards with status indicators
- Recent tickets table
- Module status cards with key metrics
- SAP GUI section headers

## Best Practices

1. **Use SAP color scheme** for consistency
2. **Include toolbar** at top of functional pages
3. **Use status badges** for state indicators
4. **Implement tree navigation** for hierarchical data
5. **Add section headers** to organize content
6. **Use tabs** for multiple views within a module
7. **Include search functionality** in master data views
8. **Show metrics/KPIs** prominently
9. **Use proper spacing** with utility classes

## Typography
- Font family: '72', 'Segoe UI', Arial, sans-serif
- Base font size: 14px
- Headers: 16-24px, font-weight 400-600

## Responsive Design
The UI is optimized for desktop SAP ERP usage (1280px+). For production, consider adding responsive breakpoints for tablet/mobile views.

## Future Enhancements
- Add SAP Fiori launchpad tiles
- Implement object page patterns
- Add smart filters
- Include SAP icon font
- Add animation transitions
- Implement keyboard shortcuts (F3, F8, etc.)
