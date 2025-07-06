import React from 'react';

interface TemplateSelectorProps {
  selectedTemplate: string;
  onChange: (template: string) => void;
}

const templates = [
  {
    id: 'template_1',
    name: 'Professional',
    description: 'Clean and modern design suitable for corporate roles',
    previewUrl: '/images/templates/template_1_preview.jpg'
  },
  {
    id: 'template_2',
    name: 'Creative',
    description: 'Eye-catching layout perfect for design and creative roles',
    previewUrl: '/images/templates/template_2_preview.jpg'
  },
  {
    id: 'template_3',
    name: 'Academic',
    description: 'Structured format ideal for research and academic positions',
    previewUrl: '/images/templates/template_3_preview.jpg'
  },
  {
    id: 'template_4',
    name: 'Minimal',
    description: 'Simple and elegant design that focuses on content',
    previewUrl: '/images/templates/template_4_preview.jpg'
  }
];

const TemplateSelector: React.FC<TemplateSelectorProps> = ({ selectedTemplate, onChange }) => {
  return (
    <div className="w-full">
      <h2 className="text-xl font-semibold mb-4">Choose a Template</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {templates.map((template) => (
          <div 
            key={template.id}
            className={`cursor-pointer rounded-lg overflow-hidden transition-all duration-300 ${
              selectedTemplate === template.id 
                ? 'ring-2 ring-offset-2 ring-cyan-400 ring-offset-gray-900 transform scale-105' 
                : 'opacity-75 hover:opacity-100'
            }`}
            onClick={() => onChange(template.id)}
          >
            <div className="relative aspect-[3/4] bg-gray-800">
              {/* Placeholder for template preview */}
              <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-900 to-gray-900">
                <span className="text-lg font-bold">{template.name}</span>
              </div>
            </div>
            <div className="p-2 text-center">
              <h3 className="font-medium text-sm">{template.name}</h3>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TemplateSelector;