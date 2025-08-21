import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { useUploadDocument } from '@/hooks/useDocuments';
import { useUploadStore } from '@/store';

interface DocumentUploadProps {
  onSuccess?: () => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onSuccess }) => {
  const { mutate: uploadDocument, isPending } = useUploadDocument();
  const { isUploading, progress, error, setUploading, setProgress, setError, reset } = useUploadStore();
  
  const [newDoc, setNewDoc] = useState({
    nombre: '',
    especialidad: '',
    tipo: '',
    archivo: null as File | null
  });

  const handleInputChange = (field: string, value: string) => {
    setNewDoc(prev => ({ ...prev, [field]: value }));
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are allowed');
      return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB');
      return;
    }

    setError(undefined);
    setNewDoc(prev => ({ 
      ...prev, 
      archivo: file,
      // Si no hay nombre, usar el nombre del archivo sin extensión
      nombre: prev.nombre || file.name.replace(/\.[^/.]+$/, "")
    }));
  }, [setError]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: isUploading || isPending,
  });

  const handleCreate = () => {
    if (newDoc.nombre && newDoc.especialidad && newDoc.tipo && newDoc.archivo) {
      setUploading(true);
      setProgress(0);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setProgress((prev: number) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Upload document
      uploadDocument(newDoc.archivo, {
        onSuccess: () => {
          setProgress(100);
          setTimeout(() => {
            reset();
            setNewDoc({ nombre: '', especialidad: '', tipo: '', archivo: null });
            onSuccess?.();
          }, 1000);
        },
        onError: (error: any) => {
          clearInterval(progressInterval);
          setError(error.response?.data?.detail || 'Upload failed');
          setUploading(false);
        },
      });
    }
  };

  return (
    <div className="space-y-6 max-w-md mx-auto">
      <div>
        <label className="block text-sm font-medium mb-2 text-gray-900">Nombre del documento</label>
        <Input
          type="text"
          value={newDoc.nombre}
          onChange={(e) => handleInputChange('nombre', e.target.value)}
          placeholder="Se completará automáticamente al subir archivo"
          className="bg-white border border-gray-300"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2 text-gray-900">Especialidad</label>
        <Select
          value={newDoc.especialidad}
          onValueChange={(value) => handleInputChange('especialidad', value)}
        >
          <SelectTrigger className="bg-white border border-gray-300">
            <SelectValue placeholder="Seleccionar especialidad" />
          </SelectTrigger>
          <SelectContent className="bg-white border border-gray-300">
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
      </div>

      <div>
        <label className="block text-sm font-medium mb-2 text-gray-900">Tipo de documento</label>
        <Select
          value={newDoc.tipo}
          onValueChange={(value) => handleInputChange('tipo', value)}
        >
          <SelectTrigger className="bg-white border border-gray-300">
            <SelectValue placeholder="Seleccionar tipo" />
          </SelectTrigger>
          <SelectContent className="bg-white border border-gray-300">
            <SelectItem value="ETs">ETs</SelectItem>
            <SelectItem value="Planos">Planos</SelectItem>
            <SelectItem value="APUs">APUs</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2 text-gray-900">Subir archivo</label>
        <div className="relative">
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragActive && !isDragReject
                ? 'border-blue-500 bg-blue-50'
                : isDragReject
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 hover:border-blue-400'
              }
              ${(isUploading || isPending) ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <input {...getInputProps()} />
            
            <div className="flex flex-col items-center gap-4">
              <Upload className="h-8 w-8 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">
                  {isDragActive && !isDragReject
                    ? 'Drop the PDF file here'
                    : isDragReject
                    ? 'File type not supported'
                    : 'Drag & drop a PDF file here, or click to select'
                  }
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Only PDF files up to 50MB are supported
                </p>
              </div>
            </div>
          </div>
        </div>
        {newDoc.archivo && (
          <p className="text-sm text-green-600 mt-2">
            📎 {newDoc.archivo.name}
          </p>
        )}
      </div>

      {/* Upload Progress */}
      {(isUploading || isPending) && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-blue-600">Uploading...</span>
            <span className="text-gray-600">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <span className="text-sm text-red-600">{error}</span>
        </div>
      )}

      {/* Success Display */}
      {progress === 100 && !error && (
        <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <span className="text-sm text-green-600">Upload completed successfully!</span>
        </div>
      )}

      <div className="flex gap-4 pt-4">
        <Button
          onClick={handleCreate}
          disabled={!newDoc.nombre || !newDoc.especialidad || !newDoc.tipo || !newDoc.archivo || isUploading || isPending}
          className="flex-1"
        >
          Crear análisis
        </Button>
        <Button
          variant="outline"
          onClick={onSuccess}
          className="flex-1"
        >
          Cancelar
        </Button>
      </div>
    </div>
  );
};

export default DocumentUpload;
