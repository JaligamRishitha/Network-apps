import React from 'react';
import ServiceRequestForm from './ServiceRequestForm';

const BusinessAppForm = () => {
  const handleSubmit = (formData) => {
    console.log('Business application help request:', formData);
    alert('Business application help request submitted successfully! Our team will contact you soon.');
  };

  return (
    <ServiceRequestForm
      title="Need help with a business application?"
      description="Click here to access Business Helpdesk. Get assistance with business applications, training, or access requests."
      formType="business"
      onSubmit={handleSubmit}
    />
  );
};

export default BusinessAppForm;