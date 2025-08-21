import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import DocumentUpload from '@/components/DocumentUpload';
import DocumentList from '@/components/DocumentList';
import DocumentDetail from '@/components/DocumentDetail';
import { Document } from '@/types';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    type: 'all',
    specialty: 'all'
  });

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document);
  };

  const handleBackToDocuments = () => {
    setSelectedDocument(null);
  };

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const Modal = ({ isOpen, onClose, title, children }: {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
  }) => {
    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
        <div className="bg-white border border-gray-200 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          <div className="p-6">
            {children}
          </div>
        </div>
      </div>
    );
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50 text-gray-900">
        <div className="max-w-7xl mx-auto p-6">
          {/* Header */}
          <div className="mb-8 p-6 bg-white rounded-lg border border-blue-500 shadow-sm">
            <h1 className="text-xl font-bold text-blue-600 mb-2">Documentos</h1>
            <p className="text-blue-500">especialidad</p>
            <p className="text-gray-600">- Tipo de documento (ETs, Planos, APUs)</p>
            <p className="text-gray-600">- archivo</p>
          </div>

          {selectedDocument ? (
            <DocumentDetail 
              document={selectedDocument} 
              onBack={handleBackToDocuments} 
            />
          ) : (
            <>
              {/* Controls */}
              <div className="mb-6 space-y-4">
                <Button 
                  className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg border border-blue-600 transition-colors flex items-center gap-2"
                  onClick={() => setShowCreateModal(true)}
                >
                  <Plus className="w-4 h-4" />
                  + crear análisis
                </Button>

                {/* Filters */}
                <div className="flex gap-4 flex-wrap">
                  <div className="flex-1 min-w-64">
                    <Input
                      type="text"
                      placeholder="Filtro por búsqueda de nombre"
                      value={filters.search}
                      onChange={(e) => handleFilterChange('search', e.target.value)}
                      className="w-full bg-white border border-gray-300"
                    />
                  </div>
                  
                  <Select
                    value={filters.specialty}
                    onValueChange={(value) => handleFilterChange('specialty', value)}
                  >
                    <SelectTrigger className="w-48 bg-white border border-gray-300">
                      <SelectValue placeholder="Filtro por especialidad" />
                    </SelectTrigger>
                    <SelectContent className="bg-white border border-gray-300">
                      <SelectItem value="all">Todas las especialidades</SelectItem>
                      <SelectItem value="Obras Provisionales">Obras Provisionales</SelectItem>
                      <SelectItem value="Arquitectura">Arquitectura</SelectItem>
                      <SelectItem value="Estructuras">Estructuras</SelectItem>
                      <SelectItem value="Instalaciones Sanitarias">Instalaciones Sanitarias</SelectItem>
                      <SelectItem value="Instalaciones Eléctricas">Instalaciones Eléctricas</SelectItem>
                      <SelectItem value="HVAC">HVAC</SelectItem>
                      <SelectItem value="GLP">GLP</SelectItem>
                      <SelectItem value="TIC">TIC</SelectItem>
                      <SelectItem value="BDC">BDC</SelectItem>
                      <SelectItem value="Mobiliario">Mobiliario</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select
                    value={filters.type}
                    onValueChange={(value) => handleFilterChange('type', value)}
                  >
                    <SelectTrigger className="w-48 bg-white border border-gray-300">
                      <SelectValue placeholder="Tipo de documento" />
                    </SelectTrigger>
                    <SelectContent className="bg-white border border-gray-300">
                      <SelectItem value="all">Todos los tipos</SelectItem>
                      <SelectItem value="ETs">ETs</SelectItem>
                      <SelectItem value="Planos">Planos</SelectItem>
                      <SelectItem value="APUs">APUs</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Document List */}
              <DocumentList 
                onDocumentSelect={handleDocumentSelect}
                filters={filters}
              />
            </>
          )}
        </div>

        {/* Create Modal */}
        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Crear Nuevo Análisis"
        >
          <DocumentUpload onSuccess={() => setShowCreateModal(false)} />
        </Modal>
      </div>
    </QueryClientProvider>
  );
}

export default App;
