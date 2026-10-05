"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, X, FileText } from "lucide-react";
import clsx from "clsx";

interface ResumeDropzoneProps {
  files: File[];
  onChange: (files: File[]) => void;
}

export default function ResumeDropzone({ files, onChange }: ResumeDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      const unique = [...files, ...accepted].filter(
        (f, i, arr) => arr.findIndex((x) => x.name === f.name) === i
      );
      onChange(unique);
    },
    [files, onChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: true,
  });

  const remove = (name: string) => onChange(files.filter((f) => f.name !== name));

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={clsx(
          "border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition",
          isDragActive
            ? "border-indigo-500 bg-indigo-50"
            : "border-gray-300 hover:border-indigo-400 hover:bg-gray-50"
        )}
      >
        <input {...getInputProps()} />
        <UploadCloud className="w-10 h-10 text-gray-400 mx-auto mb-3" />
        {isDragActive ? (
          <p className="text-indigo-600 font-medium">Drop the PDFs here…</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium">Drag & drop resume PDFs here</p>
            <p className="text-sm text-gray-400 mt-1">or click to browse — PDF only, max 10 MB each</p>
          </>
        )}
      </div>

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((f) => (
            <li key={f.name} className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-4 py-3">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <FileText className="w-4 h-4 text-indigo-500" />
                <span className="font-medium">{f.name}</span>
                <span className="text-gray-400">({(f.size / 1024).toFixed(0)} KB)</span>
              </div>
              <button onClick={() => remove(f.name)} className="text-gray-400 hover:text-red-500 transition">
                <X className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
