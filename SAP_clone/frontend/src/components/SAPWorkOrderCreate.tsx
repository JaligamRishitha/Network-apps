/**
 * SAP-Style Work Order Creation Screen
 * Mimics SAP GUI IW31 transaction - Central Header view
 */
import React, { useState } from 'react';
import '../styles/sap-theme.css';

interface Operation {
  opActivity: string;
  workCenter: string;
  plant: string;
  ctrlKey: string;
  shortText: string;
  work: number;
  workUnit: string;
  duration: number;
  durationUnit: string;
  startDate: string;
  startTime: string;
  finishDate: string;
  finishTime: string;
}

interface Component {
  item: string;
  material: string;
  description: string;
  quantity: number;
  unit: string;
  storageLocation: string;
  plant: string;
  batch: string;
  procurementType: string;
}

interface SAPWorkOrderCreateProps {
  onClose: () => void;
  onSubmit: (data: any) => void;
  equipmentList?: any[];
  embedded?: boolean;
}

const SAPWorkOrderCreate: React.FC<SAPWorkOrderCreateProps> = ({ onClose, onSubmit, equipmentList = [], embedded = false }) => {
  const [activeTab, setActiveTab] = useState('components');

  // Header form data
  const [formData, setFormData] = useState({
    orderNumber: '',
    orderType: '',
    description: '',
    sysStatus: 'CRTD',
    strt: false,
    // Person responsible
    plannerGrp: '',
    plannerGrpPlant: '',
    plannerGrpDesc: '',
    mainWorkCenter: '',
    mainWorkCenterPlant: '',
    mainWorkCenterDesc: '',
    personResp: '',
    notification: '',
    costs: '',
    currency: 'EUR',
    pmActType: '',
    pmActTypeDesc: '',
    sysCond: '',
    address: '',
    // Dates
    basicStartDate: '',
    basicFinishDate: '',
    priority: '',
    priorityDesc: '',
    revision: '',
    // Reference object
    functionalLocation: '',
    functionalLocationDesc: '',
    equipment: '',
    equipmentDesc: '',
    assembly: '',
    uii: '',
    plngPlant: '',
    busArea: '',
    // Reference
    referenceOrder: '',
    relationship: false,
    settlementRule: false,
    // First operation
    firstOpDescription: '',
    firstOpCcKey: false,
    firstOpWorkCenter: '',
    firstOpPlant: '',
    firstOpCtrlKey: '',
    firstOpActyType: '',
    firstOpPrt: false,
    firstOpWorkDuration: 0,
    firstOpWorkUnit: 'HR',
    firstOpNumber: 0,
    firstOpOprnDuration: 0,
    firstOpOprnUnit: 'HR',
    firstOpComp: false,
    firstOpPersonNo: ''
  });

  // Operations list - starts empty for initial screen
  const [operations, setOperations] = useState<Operation[]>([]);

  // Components list - starts empty for initial screen
  const [components, setComponents] = useState<Component[]>([]);

  const [showAddOperation, setShowAddOperation] = useState(false);
  const [showAddComponent, setShowAddComponent] = useState(false);
  const [newOperation, setNewOperation] = useState<Partial<Operation>>({});
  const [newComponent, setNewComponent] = useState<Partial<Component>>({});

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    const apiData = {
      assetId: formData.equipment || formData.functionalLocation,
      description: formData.description,
      orderType: formData.orderType === 'PM01' ? 'preventive' :
                 formData.orderType === 'PM02' ? 'corrective' : 'breakdown',
      priority: formData.priority === '1' ? 'critical' :
                formData.priority === '2' ? 'high' :
                formData.priority === '3' ? 'medium' : 'low',
      scheduledDate: formData.basicStartDate,
      operations: operations,
      components: components
    };

    onSubmit(apiData);
  };

  const handleAddOperation = () => {
    if (newOperation.shortText) {
      const nextNum = (operations.length + 1) * 10;
      setOperations([...operations, {
        opActivity: nextNum.toString().padStart(4, '0'),
        workCenter: newOperation.workCenter || 'MECH',
        plant: newOperation.plant || '1000',
        ctrlKey: newOperation.ctrlKey || 'PM01',
        shortText: newOperation.shortText || '',
        work: newOperation.work || 0,
        workUnit: 'HR',
        duration: newOperation.duration || 0,
        durationUnit: 'HR',
        startDate: formData.basicStartDate,
        startTime: '00:00:00',
        finishDate: formData.basicFinishDate,
        finishTime: '17:00'
      }]);
      setNewOperation({});
      setShowAddOperation(false);
    }
  };

  const handleAddComponent = () => {
    if (newComponent.material || newComponent.description) {
      const nextNum = (components.length + 1) * 10;
      setComponents([...components, {
        item: nextNum.toString().padStart(4, '0'),
        material: newComponent.material || '',
        description: newComponent.description || '',
        quantity: newComponent.quantity || 1,
        unit: newComponent.unit || 'PC',
        storageLocation: newComponent.storageLocation || '',
        plant: '1000',
        batch: '',
        procurementType: newComponent.procurementType || 'Reservation for order'
      }]);
      setNewComponent({});
      setShowAddComponent(false);
    }
  };

  const handleDeleteOperation = (index: number) => {
    setOperations(operations.filter((_, i) => i !== index));
  };

  const handleDeleteComponent = (index: number) => {
    setComponents(components.filter((_, i) => i !== index));
  };

  // SAP GUI Field component
  const SAPField = ({ label, value, onChange, width = '150px', readOnly = false, type = 'text' }: any) => (
    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
      <label style={{
        width: '100px',
        fontSize: '11px',
        color: '#333',
        textAlign: 'right',
        paddingRight: '8px'
      }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        readOnly={readOnly}
        style={{
          width,
          height: '20px',
          fontSize: '11px',
          padding: '2px 4px',
          border: '1px solid #999',
          backgroundColor: readOnly ? '#f0f0f0' : '#fff',
          fontFamily: 'Consolas, monospace'
        }}
      />
    </div>
  );

  // SAP GUI Section
  const SAPSection = ({ title, children }: any) => (
    <fieldset style={{
      border: '1px solid #999',
      margin: '8px 4px',
      padding: '8px',
      backgroundColor: '#f5f5f5'
    }}>
      <legend style={{
        fontSize: '11px',
        fontWeight: 'bold',
        color: '#333',
        padding: '0 4px'
      }}>
        {title}
      </legend>
      {children}
    </fieldset>
  );

  // Main content component
  const MainContent = () => (
    <div
      className="sap-work-order-create"
      style={{
        width: embedded ? '100%' : '95%',
        maxWidth: embedded ? '100%' : '1200px',
        height: embedded ? 'calc(100vh - 180px)' : '90vh',
        backgroundColor: '#d4d0c8',
        fontFamily: 'Tahoma, Arial, sans-serif',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
        {/* SAP Toolbar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '2px 8px',
          backgroundColor: '#f0f0f0',
          borderBottom: '1px solid #808080',
          gap: '2px'
        }}>
          <button
            onClick={handleSubmit}
            style={{
              padding: '4px 8px',
              fontSize: '14px',
              backgroundColor: '#90EE90',
              border: '1px solid #808080',
              borderRadius: '2px',
              cursor: 'pointer'
            }}
            title="Enter (Execute)"
          >
            ✓
          </button>
          <select style={{ width: '120px', height: '24px', fontSize: '11px', marginLeft: '8px' }}>
            <option value=""></option>
          </select>
          <span style={{ margin: '0 4px', color: '#808080' }}>▼</span>
          <button style={{ padding: '2px 4px', fontSize: '12px' }} title="Back">«</button>
          <button onClick={handleSubmit} style={{ padding: '2px 6px', fontSize: '11px', backgroundColor: '#f0f0f0', border: '1px solid #999' }} title="Save">💾</button>
          <div style={{ borderLeft: '1px solid #808080', height: '20px', margin: '0 4px' }}></div>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Back">🔙</button>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Exit">❌</button>
          <button onClick={onClose} style={{ padding: '2px 6px', fontSize: '11px' }} title="Cancel">🚫</button>
          <div style={{ borderLeft: '1px solid #808080', height: '20px', margin: '0 4px' }}></div>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Print">🖨️</button>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Find">🔍</button>
          <div style={{ borderLeft: '1px solid #808080', height: '20px', margin: '0 4px' }}></div>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="First Page">⏮️</button>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Previous">◀️</button>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Next">▶️</button>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Last Page">⏭️</button>
          <div style={{ borderLeft: '1px solid #808080', height: '20px', margin: '0 4px' }}></div>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Create">📝</button>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Change">✏️</button>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Display">👁️</button>
          <div style={{ flex: 1 }}></div>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Help">❓</button>
          <button style={{ padding: '2px 6px', fontSize: '11px' }} title="Customize">⚙️</button>
        </div>

        {/* Title Bar */}
        <div style={{
          backgroundColor: '#c8d8e8',
          color: '#000',
          padding: '8px 16px',
          fontSize: '16px',
          fontWeight: 'bold',
          fontStyle: 'italic',
          borderBottom: '1px solid #808080'
        }}>
          {activeTab === 'headerdata' ? 'Create Order: Initial Screen' :
           activeTab === 'operations' ? 'Create General Maintenance/ Corrective Maint : Operation Overview' :
           activeTab === 'components' ? 'Create General Maintenance/ Corrective Maint : Component Overview' :
           'Create General Maintenance/ Corrective Maint : Central Header'}
        </div>

        {/* Order Header - Only show when not on initial screen */}
        {activeTab !== 'headerdata' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            padding: '4px 8px',
            backgroundColor: '#f0f0f0',
            borderBottom: '1px solid #808080'
          }}>
            <span style={{ fontSize: '11px', marginRight: '8px' }}>Order</span>
            <input
              value={formData.orderType}
              onChange={(e) => handleChange('orderType', e.target.value)}
              style={{ width: '50px', fontSize: '11px', marginRight: '4px' }}
            />
            <input
              value={formData.orderNumber}
              readOnly
              style={{ width: '120px', fontSize: '11px', marginRight: '16px', backgroundColor: '#f0f0f0' }}
            />
            <input
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              style={{ width: '200px', fontSize: '11px', marginRight: '16px' }}
            />
            <span style={{ fontSize: '11px', marginRight: '8px' }}>Sys.Status</span>
            <input
              value={formData.sysStatus}
              readOnly
              style={{ width: '120px', fontSize: '11px', backgroundColor: '#f0f0f0', marginRight: '8px' }}
            />
            <label style={{ fontSize: '11px' }}>
              <input
                type="checkbox"
                checked={formData.strt}
                onChange={(e) => handleChange('strt', e.target.checked)}
              /> STRT
            </label>
          </div>
        )}

        {/* SAP Tabs */}
        <div style={{
          display: 'flex',
          backgroundColor: '#d4d0c8',
          borderBottom: '1px solid #808080',
          padding: '0 4px'
        }}>
          {['HeaderData', 'Operations', 'Components', 'Costs', 'Partner', 'Objects', 'Addit.Data', 'Location', 'Planning', 'Control'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab.toLowerCase().replace('.', ''))}
              style={{
                padding: '4px 12px',
                fontSize: '11px',
                backgroundColor: activeTab === tab.toLowerCase().replace('.', '') ? '#f0f0f0' : '#d4d0c8',
                border: '1px solid #808080',
                borderBottom: activeTab === tab.toLowerCase().replace('.', '') ? 'none' : '1px solid #808080',
                marginBottom: activeTab === tab.toLowerCase().replace('.', '') ? '-1px' : '0',
                cursor: 'pointer'
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          backgroundColor: '#c8d8e8',
          padding: '0'
        }}>
          {/* Header Data Tab - Initial Screen */}
          {activeTab === 'headerdata' && (
            <div style={{ padding: '16px' }}>
              {/* Header data section */}
              <div style={{
                backgroundColor: '#b8c8d8',
                padding: '4px 8px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Header data</span>
                <button style={{ padding: '2px 4px', fontSize: '10px' }}>🔄</button>
              </div>

              <div style={{ display: 'flex', gap: '40px' }}>
                {/* Left side - Form fields */}
                <div style={{ flex: 1 }}>
                  {/* Order Type */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>Order Type</label>
                    <input
                      value={formData.orderType}
                      onChange={(e) => handleChange('orderType', e.target.value)}
                      style={{
                        width: '80px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#ffffcc',
                        padding: '2px 4px'
                      }}
                    />
                    <button style={{ marginLeft: '2px', padding: '2px 6px', fontSize: '11px' }}>📋</button>
                  </div>

                  {/* Priority */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>Priority</label>
                    <select
                      value={formData.priority}
                      onChange={(e) => handleChange('priority', e.target.value)}
                      style={{
                        width: '200px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#fff'
                      }}
                    >
                      <option value=""></option>
                      <option value="1">1 - Very High</option>
                      <option value="2">2 - High</option>
                      <option value="3">3 - Medium</option>
                      <option value="4">4 - Low</option>
                    </select>
                  </div>

                  {/* Func. Loc. */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>Func. Loc.</label>
                    <input
                      value={formData.functionalLocation}
                      onChange={(e) => handleChange('functionalLocation', e.target.value)}
                      style={{
                        width: '200px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#fff',
                        padding: '2px 4px'
                      }}
                    />
                  </div>

                  {/* Equipment */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>Equipment</label>
                    <select
                      value={formData.equipment}
                      onChange={(e) => {
                        const selectedEq = equipmentList.find(eq => eq.asset_id === e.target.value);
                        handleChange('equipment', e.target.value);
                        handleChange('equipmentDesc', selectedEq?.name || '');
                      }}
                      style={{
                        width: '120px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#fff'
                      }}
                    >
                      <option value="">Select...</option>
                      {equipmentList.map(eq => (
                        <option key={eq.asset_id} value={eq.asset_id}>
                          {eq.asset_id}
                        </option>
                      ))}
                    </select>
                    <input
                      value={formData.equipmentDesc}
                      readOnly
                      style={{
                        width: '150px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#f0f0f0',
                        padding: '2px 4px',
                        marginLeft: '4px'
                      }}
                      placeholder="Equipment description"
                    />
                  </div>

                  {/* Assembly */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>Assembly</label>
                    <input
                      value={formData.assembly}
                      onChange={(e) => handleChange('assembly', e.target.value)}
                      style={{
                        width: '200px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#fff',
                        padding: '2px 4px'
                      }}
                    />
                  </div>

                  {/* UII */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>UII</label>
                    <input
                      value={formData.uii || ''}
                      onChange={(e) => handleChange('uii', e.target.value)}
                      style={{
                        width: '400px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#fff',
                        padding: '2px 4px'
                      }}
                    />
                  </div>

                  {/* Plng plant */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>Plng plant</label>
                    <input
                      value={formData.plngPlant || ''}
                      onChange={(e) => handleChange('plngPlant', e.target.value)}
                      style={{
                        width: '60px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#fff',
                        padding: '2px 4px'
                      }}
                    />
                  </div>

                  {/* Bus. Area */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>Bus. Area</label>
                    <input
                      value={formData.busArea || ''}
                      onChange={(e) => handleChange('busArea', e.target.value)}
                      style={{
                        width: '60px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#fff',
                        padding: '2px 4px'
                      }}
                    />
                  </div>

                  {/* Reference Section */}
                  <div style={{
                    backgroundColor: '#b8c8d8',
                    padding: '4px 8px',
                    marginBottom: '8px'
                  }}>
                    <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Reference</span>
                  </div>

                  {/* Order */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ width: '80px', fontSize: '12px', color: '#000' }}>Order</label>
                    <input
                      value={formData.referenceOrder || ''}
                      onChange={(e) => handleChange('referenceOrder', e.target.value)}
                      style={{
                        width: '120px',
                        height: '22px',
                        fontSize: '12px',
                        border: '1px solid #999',
                        backgroundColor: '#fff',
                        padding: '2px 4px'
                      }}
                    />
                    <div style={{ marginLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="checkbox"
                          checked={formData.relationship || false}
                          onChange={(e) => handleChange('relationship', e.target.checked)}
                        />
                        Relationship
                      </label>
                      <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="checkbox"
                          checked={formData.settlementRule || false}
                          onChange={(e) => handleChange('settlementRule', e.target.checked)}
                        />
                        Settlement Rule
                      </label>
                    </div>
                  </div>
                </div>

                {/* Right side - Icons */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <button style={{ padding: '4px', fontSize: '16px', width: '32px', height: '32px' }} title="Structure">🏗️</button>
                  <button style={{ padding: '4px', fontSize: '16px', width: '32px', height: '32px' }} title="Hierarchy">📊</button>
                  <button style={{ padding: '4px', fontSize: '16px', width: '32px', height: '32px' }} title="Info">ℹ️</button>
                </div>
              </div>
            </div>
          )}

          {/* Operations Tab */}
          {activeTab === 'operations' && (
            <div>
              <div style={{ marginBottom: '8px' }}>
                <button onClick={() => setShowAddOperation(true)} style={{ fontSize: '11px', marginRight: '4px' }}>Add</button>
                <button onClick={() => operations.length > 0 && handleDeleteOperation(operations.length - 1)} style={{ fontSize: '11px', marginRight: '4px' }}>Delete</button>
                <button style={{ fontSize: '11px' }}>Copy</button>
              </div>

              {showAddOperation && (
                <div style={{ backgroundColor: '#ffffcc', padding: '8px', marginBottom: '8px', border: '1px solid #999' }}>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    <input placeholder="Work Center" value={newOperation.workCenter || 'MECH'} onChange={(e) => setNewOperation({...newOperation, workCenter: e.target.value})}
                      style={{ width: '80px', fontSize: '11px' }} />
                    <input placeholder="Ctrl Key" value={newOperation.ctrlKey || 'PM01'} onChange={(e) => setNewOperation({...newOperation, ctrlKey: e.target.value})}
                      style={{ width: '60px', fontSize: '11px' }} />
                    <input placeholder="Operation Short Text" value={newOperation.shortText || ''} onChange={(e) => setNewOperation({...newOperation, shortText: e.target.value})}
                      style={{ width: '200px', fontSize: '11px' }} />
                    <input type="number" placeholder="Work (HR)" value={newOperation.work || ''} onChange={(e) => setNewOperation({...newOperation, work: parseFloat(e.target.value)})}
                      style={{ width: '70px', fontSize: '11px' }} />
                    <input type="number" placeholder="Duration" value={newOperation.duration || ''} onChange={(e) => setNewOperation({...newOperation, duration: parseFloat(e.target.value)})}
                      style={{ width: '70px', fontSize: '11px' }} />
                  </div>
                  <button onClick={handleAddOperation} style={{ fontSize: '11px', marginRight: '4px' }}>Save</button>
                  <button onClick={() => setShowAddOperation(false)} style={{ fontSize: '11px' }}>Cancel</button>
                </div>
              )}

              <div style={{ overflow: 'auto', height: '300px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', backgroundColor: '#fff' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#d4d0c8', position: 'sticky', top: 0 }}>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>OpAc/Sop</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '80px' }}>Work ctr</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '80px' }}>Plant/WC</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>Internal</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>S</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '200px' }}>Operation shorttext</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '30px' }}>LT</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>Work</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '40px' }}>Un</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>Durn</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '40px' }}>Un</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '80px' }}>Earl.start d</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>Earl.start t</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '80px' }}>Earliest fin d</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>Earliest fin t</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* Default operations based on SAP screenshot */}
                    {operations.length === 0 && (
                      <>
                        <tr style={{ backgroundColor: '#fff' }}>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>0010</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>MECH</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>1000 PM01</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>PM01</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', backgroundColor: '#ffffcc' }}>Prepare Oil Filter and Sealing System</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>4.000</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>HR</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>4.000</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>HR</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>30.01.2026</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>08:00</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>30.01.2026</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>12:00</td>
                        </tr>
                        <tr style={{ backgroundColor: '#f5f5f5' }}>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>0020</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>MECH</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>1000 PM01</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>PM01</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', backgroundColor: '#ffffcc' }}>Replace Oil Filter</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>1.000</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>HR</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>1.000</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>HR</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>30.01.2026</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>13:00</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>30.01.2026</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>14:00</td>
                        </tr>
                        <tr style={{ backgroundColor: '#fff' }}>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>0030</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>MECH</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>1000 PM01</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>PM01</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', backgroundColor: '#ffffcc' }}>Check and Sealing System</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>2.000</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>HR</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>2.000</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>HR</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>30.01.2026</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>14:00</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>30.01.2026</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>16:00</td>
                        </tr>
                        {/* Empty rows for SAP look */}
                        {Array.from({ length: 12 }, (_, i) => (
                          <tr key={`empty-op-${i}`} style={{ backgroundColor: (i + 3) % 2 === 0 ? '#fff' : '#f5f5f5' }}>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{String((i + 4) * 10).padStart(4, '0')}</td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          </tr>
                        ))}
                      </>
                    )}
                    {/* User-added operations */}
                    {operations.map((op, index) => (
                      <tr key={index} style={{ backgroundColor: index % 2 === 0 ? '#fff' : '#f5f5f5' }}>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.opActivity}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.workCenter}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.plant} {op.ctrlKey}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.ctrlKey}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px', backgroundColor: '#ffffcc' }}>{op.shortText}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>{op.work}.000</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.workUnit}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>{op.duration}.000</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.durationUnit}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.startDate}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.startTime}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.finishDate}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{op.finishTime}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: '8px', borderTop: '1px solid #808080', padding: '4px' }}>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>General</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Internal</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>External</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Dates</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Act Data</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Enhancement</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Ex.Factor</button>
                <button style={{ fontSize: '11px' }}>Catalog</button>
              </div>
            </div>
          )}

          {/* Components Tab */}
          {activeTab === 'components' && (
            <div>
              <div style={{ marginBottom: '8px' }}>
                <button onClick={() => setShowAddComponent(true)} style={{ fontSize: '11px', marginRight: '4px' }}>Add</button>
                <button onClick={() => components.length > 0 && handleDeleteComponent(components.length - 1)} style={{ fontSize: '11px', marginRight: '4px' }}>Delete</button>
                <button style={{ fontSize: '11px' }}>Copy</button>
              </div>

              {showAddComponent && (
                <div style={{ backgroundColor: '#ffffcc', padding: '8px', marginBottom: '8px', border: '1px solid #999' }}>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    <input placeholder="Material" value={newComponent.material || ''} onChange={(e) => setNewComponent({...newComponent, material: e.target.value})}
                      style={{ width: '80px', fontSize: '11px' }} />
                    <input placeholder="Description" value={newComponent.description || ''} onChange={(e) => setNewComponent({...newComponent, description: e.target.value})}
                      style={{ width: '150px', fontSize: '11px' }} />
                    <input type="number" placeholder="Qty" value={newComponent.quantity || ''} onChange={(e) => setNewComponent({...newComponent, quantity: parseFloat(e.target.value)})}
                      style={{ width: '60px', fontSize: '11px' }} />
                    <input placeholder="Unit" value={newComponent.unit || 'PC'} onChange={(e) => setNewComponent({...newComponent, unit: e.target.value})}
                      style={{ width: '40px', fontSize: '11px' }} />
                    <input placeholder="Storage Loc" value={newComponent.storageLocation || '0001'} onChange={(e) => setNewComponent({...newComponent, storageLocation: e.target.value})}
                      style={{ width: '80px', fontSize: '11px' }} />
                    <select value={newComponent.procurementType || 'Reservation for order'} onChange={(e) => setNewComponent({...newComponent, procurementType: e.target.value})}
                      style={{ fontSize: '11px' }}>
                      <option value="Reservation for order">Reservation for order</option>
                      <option value="PReq for order">PReq for order</option>
                    </select>
                  </div>
                  <button onClick={handleAddComponent} style={{ fontSize: '11px', marginRight: '4px' }}>Save</button>
                  <button onClick={() => setShowAddComponent(false)} style={{ fontSize: '11px' }}>Cancel</button>
                </div>
              )}

              <div style={{ overflow: 'auto', height: '300px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', backgroundColor: '#fff' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#d4d0c8', position: 'sticky', top: 0 }}>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '50px' }}>Item</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '100px' }}>Component</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '200px' }}>Description</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '30px' }}>L/T</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '80px' }}>Required Qty</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '40px' }}>UM</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '30px' }}>IC</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '30px' }}>IS</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>SLoc</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '50px' }}>Plnt</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '60px' }}>OpAc</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '80px' }}>Batch</th>
                      <th style={{ border: '1px solid #808080', padding: '4px', width: '150px' }}>Procurement Ty.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* Default components based on SAP screenshot */}
                    {components.length === 0 && (
                      <>
                        <tr style={{ backgroundColor: '#fff' }}>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>0010</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>P-F100</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>Pump</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'center' }}>🔧</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>1</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>PC</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>L</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>0001</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>1000</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>0010</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>Reservation for order</td>
                        </tr>
                        <tr style={{ backgroundColor: '#f5f5f5' }}>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>0020</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>E-SEAL</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>Electronic</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'center' }}>🔧</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>1</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>PC</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>M</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>1000</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>0020</td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>PReq for order</td>
                        </tr>
                        {/* Empty rows for SAP look */}
                        {Array.from({ length: 15 }, (_, i) => (
                          <tr key={`empty-${i}`} style={{ backgroundColor: i % 2 === 0 ? '#fff' : '#f5f5f5' }}>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{String((i + 3) * 10).padStart(4, '0')}</td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                            <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                          </tr>
                        ))}
                      </>
                    )}
                    {/* User-added components */}
                    {components.map((comp, index) => (
                      <tr key={index} style={{ backgroundColor: index % 2 === 0 ? '#fff' : '#f5f5f5' }}>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.item}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.material}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.description}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'center' }}>🔧</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px', textAlign: 'right' }}>{comp.quantity}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.unit}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>L</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}></td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.storageLocation}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.plant}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.item}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.batch}</td>
                        <td style={{ border: '1px solid #ccc', padding: '2px 4px' }}>{comp.procurementType}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: '8px', borderTop: '1px solid #808080', padding: '4px' }}>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Gen.Data</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Purch.</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>List</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Graph</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Asset</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Material Where-Used</button>
                <button style={{ fontSize: '11px', marginRight: '4px' }}>Repl</button>
                <button style={{ fontSize: '11px' }}>Catalog</button>
                <button style={{ fontSize: '11px' }}>Catalog</button>
              </div>
            </div>
          )}

          {/* Other Tabs - Placeholder */}
          {['costs', 'partner', 'objects', 'additdata', 'location', 'planning', 'control'].includes(activeTab) && (
            <div style={{ padding: '40px', textAlign: 'center', color: '#666', fontSize: '12px' }}>
              <div style={{ marginBottom: '16px', fontSize: '24px' }}>📋</div>
              {activeTab.charAt(0).toUpperCase() + activeTab.slice(1).replace('data', '. Data')} tab - Data will be displayed here
            </div>
          )}
        </div>

        {/* Status Bar */}
        <div style={{
          backgroundColor: '#d4d0c8',
          borderTop: '1px solid #808080',
          padding: '4px 8px',
          fontSize: '11px',
          display: 'flex',
          justifyContent: 'space-between'
        }}>
          <span>Ready</span>
          <span>SAP</span>
        </div>
      </div>
  );

  // Return embedded or modal version
  if (embedded) {
    return <MainContent />;
  }

  return (
    <div className="sap-modal-overlay" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()}>
        <MainContent />
      </div>
    </div>
  );
};

export default SAPWorkOrderCreate;
