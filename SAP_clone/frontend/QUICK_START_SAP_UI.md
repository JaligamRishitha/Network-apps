# Quick Start: SAP UI Components

## Getting Started

### 1. Import the SAP Theme
The theme is already imported in `main.tsx`:
```tsx
import './styles/sap-theme.css'
```

### 2. Basic Page Structure
```tsx
import React from 'react';
import '../styles/sap-theme.css';

const MyPage: React.FC = () => {
  return (
    <div>
      {/* Toolbar */}
      <div className="sap-toolbar">
        <button className="sap-toolbar-button primary">
          <span>📝</span> Create
        </button>
        <button className="sap-toolbar-button">
          <span>👁️</span> Display
        </button>
      </div>

      {/* Main Container */}
      <div className="sap-gui-container">
        <div className="sap-gui-section">
          My Module - Master Data
        </div>

        {/* Your content here */}
      </div>
    </div>
  );
};
```

## Common Components

### Section Header
```tsx
<div className="sap-gui-section">
  Plant Maintenance - Equipment Master Data
</div>
```

### Toolbar with Buttons
```tsx
<div className="sap-toolbar">
  <button className="sap-toolbar-button primary">
    <span>📝</span> Create
  </button>
  <button className="sap-toolbar-button">
    <span>✏️</span> Change
  </button>
  <button className="sap-toolbar-button">
    <span>👁️</span> Display
  </button>
  <div style={{ width: '1px', height: '24px', backgroundColor: '#d9d9d9' }}></div>
  <button className="sap-toolbar-button">
    <span>🔍</span> Find
  </button>
</div>
```

### Status Badges
```tsx
<span className="sap-status success">Approved</span>
<span className="sap-status warning">Pending</span>
<span className="sap-status error">Rejected</span>
<span className="sap-status info">In Progress</span>
```

### Data Table
```tsx
<table className="sap-table">
  <thead>
    <tr>
      <th>ID</th>
      <th>Description</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style={{ fontWeight: 600, color: '#0a6ed1' }}>001</td>
      <td>Item Description</td>
      <td>
        <span className="sap-status success">Active</span>
      </td>
    </tr>
  </tbody>
</table>
```

### Tabs
```tsx
const [activeTab, setActiveTab] = useState('tab1');

<div className="sap-gui-tabs">
  <div 
    className={`sap-gui-tab ${activeTab === 'tab1' ? 'active' : ''}`}
    onClick={() => setActiveTab('tab1')}
  >
    General Data
  </div>
  <div 
    className={`sap-gui-tab ${activeTab === 'tab2' ? 'active' : ''}`}
    onClick={() => setActiveTab('tab2')}
  >
    Details
  </div>
</div>

{activeTab === 'tab1' && (
  <div className="sap-gui-panel">
    {/* Tab 1 content */}
  </div>
)}
```

### Form Fields
```tsx
<div className="sap-form-group">
  <label className="sap-form-label">Material Number</label>
  <input 
    type="text" 
    className="sap-form-input" 
    placeholder="Enter material number..."
  />
</div>
```

### KPI Cards
```tsx
<div className="sap-grid sap-grid-4">
  <div style={{ 
    padding: '16px', 
    backgroundColor: '#e5f3ff', 
    borderRadius: '4px', 
    textAlign: 'center' 
  }}>
    <div style={{ fontSize: '12px', color: '#6a6d70' }}>Total Active</div>
    <div style={{ fontSize: '32px', fontWeight: 600, color: '#0a6ed1' }}>24</div>
  </div>
  {/* More cards... */}
</div>
```

### Fiori Card
```tsx
<div className="sap-fiori-card">
  <div className="sap-fiori-card-header">
    <h3 className="sap-fiori-card-title">Card Title</h3>
  </div>
  <div className="sap-fiori-card-content">
    {/* Card content */}
  </div>
</div>
```

### Tree Navigation
```tsx
<div className="sap-tree">
  <div className="sap-tree-item" style={{ fontWeight: 600 }}>
    📁 Main Menu
  </div>
  <div 
    className={`sap-tree-item ${selected === 'item1' ? 'selected' : ''}`}
    onClick={() => setSelected('item1')}
    style={{ paddingLeft: '24px' }}
  >
    📄 Sub Item 1
  </div>
</div>
```

## Layout Utilities

### Grid Layouts
```tsx
<div className="sap-grid sap-grid-2">  {/* 2 columns */}
  <div>Column 1</div>
  <div>Column 2</div>
</div>

<div className="sap-grid sap-grid-3">  {/* 3 columns */}
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>
```

### Flex Layouts
```tsx
<div className="sap-flex">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<div className="sap-flex-between">
  <div>Left</div>
  <div>Right</div>
</div>
```

## Color Reference

### CSS Variables
```css
var(--sap-shell-bg)      /* #354a5f - Dark blue */
var(--sap-shell-active)  /* #0a6ed1 - SAP blue */
var(--sap-success)       /* #107e3e - Green */
var(--sap-warning)       /* #e9730c - Orange */
var(--sap-error)         /* #bb0000 - Red */
var(--sap-info)          /* #0a6ed1 - Blue */
```

### Direct Colors
```tsx
// Primary SAP Blue
color: '#0a6ed1'

// Success Green
color: '#107e3e'

// Warning Orange
color: '#e9730c'

// Error Red
color: '#bb0000'

// Text Colors
color: '#32363a'  // Primary text
color: '#6a6d70'  // Secondary text
```

## Tips & Best Practices

1. **Always use SAP classes** for consistency
2. **Use status badges** for state indicators
3. **Include toolbars** on functional pages
4. **Add section headers** to organize content
5. **Use proper spacing** with utility classes
6. **Make IDs/codes blue** (#0a6ed1) and bold
7. **Right-align numbers** in tables
8. **Use icons** in toolbar buttons
9. **Add hover states** for interactive elements
10. **Keep it simple** - SAP UI is clean and functional

## Examples in the Codebase

- **Dashboard**: `frontend/src/pages/Dashboard.tsx`
- **Plant Maintenance**: `frontend/src/pages/PM.tsx`
- **Materials Management**: `frontend/src/pages/MM.tsx`
- **Financial Accounting**: `frontend/src/pages/FI.tsx`
- **Layout**: `frontend/src/components/Layout.tsx`

## Demo Page

Open `frontend/public/sap-ui-demo.html` in your browser to see all components in action!

## Need Help?

Check the full style guide: `frontend/SAP_UI_GUIDE.md`
