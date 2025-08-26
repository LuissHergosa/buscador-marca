import { useMemo } from 'react';
import { Trash2, Eye, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useDocuments, useDeleteDocument } from '@/hooks/useDocuments';
import { useProcessingStatusStore } from '@/store';
import { Document } from '@/types';

interface DocumentListProps {
  onDocumentSelect: (document: Document) => void;
  filters: {
    search: string;
    type: string;
    specialty: string;
  };
}

const DocumentList: React.FC<DocumentListProps> = ({ onDocumentSelect, filters }) => {
  const { data: documents = [], isLoading: loading, error } = useDocuments();
  const { statuses } = useProcessingStatusStore();
  const { mutate: deleteDocument } = useDeleteDocument();

  // Filter documents
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc: Document) => {
      const matchesSearch = filters.search === '' || 
        doc.filename.toLowerCase().includes(filters.search.toLowerCase());
      const matchesType = filters.type === 'all' || filters.type === '' || doc.filename.toLowerCase().includes(filters.type.toLowerCase());
      const matchesSpecialty = filters.specialty === 'all' || filters.specialty === '' || doc.filename.toLowerCase().includes(filters.specialty.toLowerCase());
      return matchesSearch && matchesType && matchesSpecialty;
    });
  }, [documents, filters]);

  // Get status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">Completado</Badge>;
      case 'processing':
        return <Badge className="bg-blue-100 text-blue-800">Procesando</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Fallido</Badge>;
      case 'completed_with_errors':
        return <Badge className="bg-yellow-100 text-yellow-800">Completado con errores</Badge>;
      case 'cancelled':
        return <Badge className="bg-gray-100 text-gray-800">Cancelado</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">{status}</Badge>;
    }
  };

  // Handle delete
  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('¿Estás seguro de que quieres eliminar este documento?')) {
      deleteDocument(id);
    }
  };

  // Loading State
  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-gray-600">Cargando documentos...</p>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span>{error instanceof Error ? error.message : 'Error desconocido'}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
      {filteredDocuments.map((document: Document) => {
        const processingStatus = statuses[document.id];
        
        return (
          <Card
            key={document.id}
            className="bg-white border border-gray-200 rounded-lg p-5 hover:border-blue-500 transition-colors relative cursor-pointer group"
            onClick={() => onDocumentSelect(document)}
          >
            {/* Delete Button */}
            <button
              onClick={(e) => handleDelete(document.id, e)}
              className="absolute top-2 right-2 p-1 text-gray-400 hover:text-red-500 hover:bg-gray-100 rounded transition-colors"
              title="Eliminar documento"
            >
              <Trash2 className="w-4 h-4" />
            </button>

            <div className="flex justify-between items-start mb-3 pr-8">
              <h3 className="font-semibold text-gray-900 text-sm leading-tight">{document.filename}</h3>
              {document.status === 'completed' && <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 ml-2" />}
            </div>
            
            <p className="text-blue-600 text-xs mb-2">
              <span className="font-medium">Estado:</span> {getStatusBadge(document.status)}
            </p>
            
            <p className="text-blue-500 text-xs mb-2">
              <span className="font-medium">Páginas procesadas:</span> {document.total_pages}
            </p>
            
            <p className="text-gray-500 text-xs mb-4">
              <span className="font-medium">Resultados:</span> {document.results?.reduce((total, result) => total + (result.brands_detected?.length || 0), 0) || 0}
            </p>

            {/* Processing Progress */}
            {document.status === 'processing' && processingStatus && (
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-blue-600">Procesando...</span>
                  <span className="text-gray-600">{Math.round(processingStatus.progress_percentage)}%</span>
                </div>
                <Progress 
                  value={processingStatus.progress_percentage} 
                  className="h-2" 
                />
                <p className="text-xs text-gray-500">
                  {processingStatus.processed_pages} de {processingStatus.total_pages} páginas
                </p>
              </div>
            )}
            
            <Button
              onClick={(e) => {
                e.stopPropagation();
                onDocumentSelect(document);
              }}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded text-sm transition-colors flex items-center justify-center gap-2"
            >
              <Eye className="w-4 h-4" />
              ver análisis
            </Button>
          </Card>
        );
      })}

      {/* Empty State */}
      {!loading && !error && filteredDocuments.length === 0 && (
        <div className="col-span-full text-center text-gray-500 mt-12">
          <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg">No se encontraron documentos con los filtros aplicados</p>
        </div>
      )}
    </div>
  );
};

export default DocumentList;
