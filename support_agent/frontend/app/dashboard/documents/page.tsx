'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import { Document } from '@/types';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await apiService.listDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch documents.');
    } finally {
      setLoading(false);
    }
  };

  const handleFile = async (file: File) => {
    setError(null);
    setSuccess(null);

    // Validate type
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF documents are supported.');
      return;
    }

    // Validate size (10MB limit)
    const MAX_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setError('File size exceeds the 10MB limit.');
      return;
    }

    setUploading(true);
    try {
      await apiService.uploadDocument(file);
      setSuccess(`Document "${file.name}" uploaded and queued for processing!`);
      fetchDocuments();
    } catch (err: any) {
      setError(err.message || 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document? All associated vector embeddings will be permanently removed.')) {
      return;
    }

    setError(null);
    setSuccess(null);
    try {
      await apiService.deleteDocument(id);
      setSuccess('Document successfully deleted.');
      setDocuments(prev => prev.filter(doc => doc.id !== id));
    } catch (err: any) {
      setError(err.message || 'Failed to delete document.');
    }
  };

  // Helper for size display
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto w-full space-y-8 animate-fade-in">
      <div className="flex flex-col gap-1.5">
        <h2 className="text-2xl font-black text-slate-900">Knowledge Base</h2>
        <p className="text-xs text-slate-500">
          Upload guidelines, documentation, or FAQs to train your Support Agent.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs px-4 py-3.5 rounded-xl">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs px-4 py-3.5 rounded-xl">
          {success}
        </div>
      )}

      {/* Drag & Drop Upload Zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center transition-all ${
          dragActive
            ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01]'
            : 'border-slate-200 hover:border-indigo-500/50 bg-slate-50'
        }`}
      >
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-2xl text-indigo-600 mb-4">
          📥
        </div>
        <p className="text-sm font-semibold text-slate-800 mb-1">
          {uploading ? 'Processing Document...' : 'Drag and drop your PDF here'}
        </p>
        <p className="text-xs text-slate-500 mb-4">or click to browse your local files</p>
        
        <input
          type="file"
          id="file-upload-input"
          accept=".pdf"
          onChange={handleFileInputChange}
          disabled={uploading}
          className="hidden"
        />
        
        <label
          htmlFor="file-upload-input"
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-500/20 transition-colors cursor-pointer disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : 'Select PDF File'}
        </label>
        
        <p className="text-[10px] text-slate-500 mt-3">Maximum file size: 10MB (PDF Only)</p>
      </div>

      {/* Documents List Table */}
      <div className="glass-panel rounded-2xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-800">Uploaded Documents</h3>
          <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full font-semibold">
            {documents.length} Files
          </span>
        </div>

        {loading ? (
          <div className="p-12 flex justify-center">
            <div className="w-8 h-8 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center">
            <span className="text-3xl mb-3">📁</span>
            <p className="text-sm text-slate-700 font-semibold mb-1">No documents uploaded yet</p>
            <p className="text-xs text-slate-500">Your startup knowledge base is empty. Upload your first PDF above.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                  <th className="px-6 py-4">Filename</th>
                  <th className="px-6 py-4">Size</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Upload Date</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-800 max-w-xs truncate" title={doc.filename}>
                      {doc.filename}
                    </td>
                    <td className="px-6 py-4">{formatBytes(doc.file_size)}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold ${
                          doc.status === 'processed'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : doc.status === 'processing'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200 animate-pulse'
                            : 'bg-red-50 text-red-700 border border-red-200'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            doc.status === 'processed'
                              ? 'bg-emerald-400'
                              : doc.status === 'processing'
                              ? 'bg-amber-400 animate-pulse'
                              : 'bg-red-400'
                          }`}
                        />
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-2 text-slate-500 hover:text-red-600 transition-colors hover:bg-slate-100 rounded-lg cursor-pointer"
                        title="Delete Document"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
