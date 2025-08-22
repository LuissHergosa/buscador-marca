import { useState } from 'react';
import { CheckCircle, Eye, FileText, Calendar, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Document, BrandDetection } from '@/types';
import { useDocumentResults, useUpdateBrandReviewStatus } from '@/hooks/useDocuments';

interface DocumentDetailProps {
  document: Document;
  onBack: () => void;
}

const DocumentDetail: React.FC<DocumentDetailProps> = ({ document, onBack }) => {
  const [activeTab, setActiveTab] = useState('por-revisar');

  // Fetch document results from API
  const { data: documentWithResults, isLoading: loadingResults } = useDocumentResults(document.id);
  const { mutate: updateBrandReviewStatus, isPending: isUpdating } = useUpdateBrandReviewStatus();

  // Get results from the API response
  const results = documentWithResults?.results || document.results || [];

  // Separate results into por revisar (not reviewed) and revisado (reviewed)
  const elementosPorRevisar = results.flatMap((result: BrandDetection) =>
    result.brands_detected
      .filter((brand: string) => !result.brands_review_status[brand])
      .map((brand: string, index: number) => ({
        id: `${result.page_number}-${brand}`,
        nombre: brand,
        pagina: result.page_number,
        pageNumber: result.page_number,
        brandName: brand
      }))
  );

  const elementosRevisados = results.flatMap((result: BrandDetection) =>
    result.brands_detected
      .filter((brand: string) => result.brands_review_status[brand])
      .map((brand: string, index: number) => ({
        id: `${result.page_number}-${brand}`,
        nombre: brand,
        pagina: result.page_number,
        pageNumber: result.page_number,
        brandName: brand
      }))
  );

  const handleToggleReviewStatus = (elemento: any, newStatus: boolean) => {
    updateBrandReviewStatus({
      document_id: document.id,
      page_number: elemento.pageNumber,
      brand_name: elemento.brandName,
      is_reviewed: newStatus
    });
  };

  // Loading state
  if (loadingResults) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600 text-lg">Cargando análisis del documento...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Document Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <FileText className="w-8 h-8 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">{document.filename}</h2>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>Subido el {new Date(document.upload_date).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>{document.total_pages} páginas</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500 mb-1">Estado del documento</div>
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${document.status === 'completed'
              ? 'bg-green-100 text-green-800'
              : document.status === 'processing'
                ? 'bg-blue-100 text-blue-800'
                : 'bg-gray-100 text-gray-800'
              }`}>
              {document.status === 'completed' ? 'Completado' :
                document.status === 'processing' ? 'Procesando' :
                  document.status}
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Results */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('por-revisar')}
            className={`flex-1 px-6 py-4 font-medium transition-colors relative ${activeTab === 'por-revisar'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Eye className="w-5 h-5" />
              <span>Por Revisar</span>
              <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded-full">
                {elementosPorRevisar.length}
              </span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('revisado')}
            className={`flex-1 px-6 py-4 font-medium transition-colors relative ${activeTab === 'revisado'
              ? 'text-green-600 border-b-2 border-green-600 bg-green-50'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
          >
            <div className="flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5" />
              <span>Revisado</span>
              <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded-full">
                {elementosRevisados.length}
              </span>
            </div>
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'por-revisar' && (
            <div className="space-y-4">

              {elementosPorRevisar.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-400" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">¡Excelente trabajo!</h4>
                  <p className="text-gray-500">Todas las marcas han sido revisadas</p>
                </div>
              ) : (
                <div className="grid gap-3">
                  {elementosPorRevisar.map((elemento) => (
                    <div
                      key={elemento.id}
                      onClick={() => handleToggleReviewStatus(elemento, true)}
                      className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors cursor-pointer group"
                      title="Click para marcar como revisado"
                    >
                      <div className="flex items-center gap-4">
                        <div>
                          <div className="font-medium text-gray-900">{elemento.nombre}</div>
                          <div className="text-sm text-gray-500">Página {elemento.pagina}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-blue-600">
                        <span className="text-sm font-medium">Marcar como revisado</span>
                        <CheckCircle className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'revisado' && (
            <div className="space-y-4">
              {elementosRevisados.length === 0 ? (
                <div className="text-center py-12">
                  <Eye className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Sin marcas revisadas</h4>
                  <p className="text-gray-500">Las marcas revisadas aparecerán aquí</p>
                </div>
              ) : (
                <div className="grid gap-3">
                  {elementosRevisados.map((elemento) => (
                    <div
                      key={elemento.id}
                      onClick={() => handleToggleReviewStatus(elemento, false)}
                      className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors cursor-pointer group"
                      title="Click para marcar como no revisado"
                    >
                      <div className="flex items-center gap-4">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <div>
                          <div className="font-medium text-gray-900">{elemento.nombre}</div>
                          <div className="text-sm text-gray-500">Página {elemento.pagina}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-green-600">
                        <span className="text-sm font-medium">Click para deshacer</span>
                        <Eye className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3">
        <Button
          variant="outline"
          onClick={onBack}
          className="px-6 py-2"
        >
          Cerrar
        </Button>
      </div>
    </div>
  );
};

export default DocumentDetail;
