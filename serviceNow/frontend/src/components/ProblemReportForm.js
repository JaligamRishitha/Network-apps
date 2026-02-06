import React from 'react';
import ServiceRequestForm from './ServiceRequestForm';

const ProblemReportForm = () => {
  const handleSubmit = (formData) => {
    console.log('Problem report:', formData);
    alert('Problem report submitted successfully! You will receive a ticket number via email shortly.');
  };

  return (
    <ServiceRequestForm
      title="Got A Problem"
      description="Describe the problem you are experiencing"
      formType="problem"
      onSubmit={handleSubmit}
    />
  );
};

export default ProblemReportForm;