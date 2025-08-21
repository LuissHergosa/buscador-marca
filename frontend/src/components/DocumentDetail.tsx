import { useState } from 'react';
import { ArrowLeft, CheckCircle, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Document } from '@/types';

interface DocumentDetailProps {
  document: Document;
  onBack: () => void;
}

const DocumentDetail: React.FC<DocumentDetailProps> = ({ document, onBack }) => {
  const [activeTab, setActiveTab] = useState('por-revisar');
  
  // Fetch document results
  // const { data: results, isLoading: loadingResults } = useDocumentResults(document.id);

  // Mock data for elements - in real implementation, this would come from the API
  const [elementosPorRevisar, setElementosPorRevisar] = useState([
    { id: 1, nombre: '[elemento marca A]', pagina: 'página 1' },
    { id: 2, nombre: '[elemento marca B]', pagina: 'página 3' },
    { id: 3, nombre: '[elemento marca C]', pagina: 'página 5' },
  ]);
  const [elementosRevisados, setElementosRevisados] = useState([
    { id: 4, nombre: '[elemento marca D]', pagina: 'página 2' },
    { id: 5, nombre: '[elemento marca E]', pagina: 'página 4' },
  ]);

  const moverARevisado = (elemento: any) => {
    // Remover de por revisar
    setElementosPorRevisar(prev => prev.filter(el => el.id !== elemento.id));
    // Agregar a revisados
    setElementosRevisados(prev => [...prev, elemento]);
  };

  const moverAPorRevisar = (elemento: any) => {
    // Remover de revisados
    setElementosRevisados(prev => prev.filter(el => el.id !== elemento.id));
    // Agregar a por revisar
    setElementosPorRevisar(prev => [...prev, elemento]);
  };

  const toggleRevisado = () => {
    // This would update the document status in the backend
    console.log('Marcar como revisado:', document.id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button 
          variant="ghost" 
          onClick={onBack} 
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver a Documentos
        </Button>
        
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{document.filename}</h1>
          <p className="text-gray-600">
            Subido el {new Date(document.upload_date).toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Analysis Modal Content */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => setActiveTab('por-revisar')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'por-revisar'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Por Revisar
          </button>
          <button
            onClick={() => setActiveTab('revisado')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'revisado'
                ? 'border-b-2 border-green-500 text-green-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Revisado
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'por-revisar' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-700 mb-4">ELEMENTOS POR REVISAR</h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center text-sm">
                <span className="text-orange-600 font-medium">Nombre</span>
                <span className="text-blue-600 font-medium">Tipo documento</span>
              </div>
              
              <div className="flex justify-between items-center text-sm">
                <span className="text-orange-600 font-medium">Especialidad</span>
                <span className="text-gray-600">Nombre del archivo</span>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-white rounded text-sm border border-blue-200">
                  <span className="text-blue-600 font-medium">por revisar</span>
                  <span className="text-gray-500">click para revisar</span>
                </div>
                
                {elementosPorRevisar.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No hay elementos por revisar</p>
                  </div>
                ) : (
                  elementosPorRevisar.map((elemento) => (
                    <div 
                      key={elemento.id}
                      onClick={() => moverARevisado(elemento)}
                      className="flex items-center p-2 bg-white rounded hover:bg-blue-50 transition-colors cursor-pointer group border border-blue-200"
                    >
                      <div className="w-4 h-4 border-2 border-blue-500 rounded mr-3 group-hover:bg-blue-500 transition-colors"></div>
                      <span className="text-blue-600 text-sm">{elemento.nombre}</span>
                      <span className="text-gray-500 ml-auto text-sm">{elemento.pagina}</span>
                      <div className="w-4 h-4 bg-gray-300 rounded ml-2 group-hover:bg-blue-400 transition-colors"></div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'revisado' && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-700 mb-4">ELEMENTOS REVISADOS</h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center text-sm">
                <span className="text-orange-600 font-medium">Nombre</span>
                <span className="text-green-600 font-medium">Tipo documento</span>
              </div>
              
              <div className="flex justify-between items-center text-sm">
                <span className="text-orange-600 font-medium">Especialidad</span>
                <span className="text-gray-600">Nombre del archivo</span>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-white rounded text-sm border border-green-200">
                  <span className="text-green-600 font-medium">revisado</span>
                  <span className="text-gray-500">click para deshacer</span>
                </div>
                
                {elementosRevisados.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Eye className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No hay elementos revisados</p>
                  </div>
                ) : (
                  elementosRevisados.map((elemento) => (
                    <div 
                      key={elemento.id}
                      onClick={() => moverAPorRevisar(elemento)}
                      className="flex items-center p-2 bg-white rounded hover:bg-green-50 transition-colors cursor-pointer group border border-green-200"
                    >
                      <CheckCircle className="w-4 h-4 text-green-600 mr-3 group-hover:text-green-500 transition-colors" />
                      <span className="text-green-600 text-sm group-hover:text-green-500 transition-colors">{elemento.nombre}</span>
                      <span className="text-gray-500 ml-auto text-sm">{elemento.pagina}</span>
                      <CheckCircle className="w-4 h-4 text-green-600 ml-2 group-hover:text-green-500 transition-colors" />
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 flex gap-4 justify-end">
          <Button
            onClick={toggleRevisado}
            className="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded transition-colors"
          >
            Marcar como revisado
          </Button>
          <Button
            variant="outline"
            onClick={onBack}
            className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-6 py-2 rounded transition-colors"
          >
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DocumentDetail;
