'use client';

import { useState, useEffect } from 'react';
import { FileText, CheckCircle, XCircle, Trash2 } from 'lucide-react';
import ResultsDisplay, { type StreamEvent } from "@/components/ResultsDisplay";

export default function HomePage() {
  const [answerKeyFile, setAnswerKeyFile] = useState<File | null>(null);
  const [studentSheetFiles, setStudentSheetFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, fileType: 'key' | 'student') => {
    if (e.target.files) {
      if (fileType === 'key') {
        setAnswerKeyFile(e.target.files[0]);
      } else {
        const newFiles = Array.from(e.target.files);
        setStudentSheetFiles(prevFiles => {
          const existingFileNames = new Set(prevFiles.map(f => f.name));
          const uniqueNewFiles = newFiles.filter(f => !existingFileNames.has(f.name));
          return [...prevFiles, ...uniqueNewFiles];
        });
      }
    }
    e.target.value = '';
  };

  const handleRemoveStudentFile = (fileNameToRemove: string) => {
    setStudentSheetFiles(prevFiles => prevFiles.filter(file => file.name !== fileNameToRemove));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answerKeyFile || studentSheetFiles.length === 0) {
      setError("Lütfen hem cevap anahtarını hem de en az bir öğrenci kağıdını seçin.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setJobId(null);
    setEvents([]);

    const formData = new FormData();
    formData.append('answer_key', answerKeyFile);
    studentSheetFiles.forEach(file => formData.append('student_sheets', file));

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/jobs`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error(`API Hatası: ${response.statusText}`);
      const result = await response.json();
      setJobId(result.job_id);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || "Bilinmeyen bir hata oluştu.");
      setIsLoading(false);
    }
  };

  const [events, setEvents] = useState<StreamEvent[]>([]);
  useEffect(() => {
    if (!jobId) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
    const wsUrl = apiUrl.replace(/^http/, 'ws');
    const socket = new WebSocket(`${wsUrl}/api/jobs/${jobId}/ws`);
    socket.onopen = () => {
      console.log("WebSocket bağlantısı kuruldu");
      setIsLoading(false);
    };
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const type = payload.event;
        const payloadData = payload.data;
        setEvents((prev) => [ ...prev, { type, payload: payloadData, timestamp: new Date().toISOString() } ]);
  } catch (err) { console.warn("WebSocket verisi JSON değil:", event.data, err); }
    };
    socket.onerror = (err) => { console.error("WebSocket hatası:", err); setError("Bağlantı hatası oluştu."); };
    socket.onclose = () => { console.log("WebSocket bağlantısı kapandı."); };
    return () => { socket.close(); };
  }, [jobId]);

  if (!jobId) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-xl w-full bg-white p-8 rounded-lg shadow-md">
            <h1 className="text-2xl font-bold text-center text-gray-800 mb-6">Yapay Zeka Sınav Değerlendirme Sistemi</h1>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">1. Cevap Anahtarını Yükle (PDF)</label>
              <div className="mt-1 flex items-center space-x-4 p-4 border-2 border-gray-300 border-dashed rounded-md">
                <FileText className="h-12 w-12 text-gray-400" />
                <label htmlFor="answer-key-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500">
                  <span>Dosya Seç</span>
                  <input id="answer-key-upload" type="file" accept=".pdf" className="sr-only" onChange={(e) => handleFileChange(e, 'key')} />
                </label>
                {answerKeyFile && <p className="text-sm text-gray-600">{answerKeyFile.name} <CheckCircle className="inline h-4 w-4 text-green-500"/></p>}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">2. Öğrenci Kağıtlarını Yükle (Bir veya Birden Fazla PDF)</label>
              <div className="mt-1 p-4 border-2 border-gray-300 border-dashed rounded-md">
                <div className="flex items-center space-x-4">
                  <FileText className="h-12 w-12 text-gray-400" />
                  <label htmlFor="student-sheets-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500">
                    <span>Dosya Ekle</span>
                    <input id="student-sheets-upload" type="file" accept=".pdf" multiple className="sr-only" onChange={(e) => handleFileChange(e, 'student')} />
                  </label>
                  {studentSheetFiles.length > 0 && <p className="text-sm text-gray-600">{studentSheetFiles.length} dosya seçildi.</p>}
                </div>
                {studentSheetFiles.length > 0 && (
                  <ul className="mt-4 space-y-2">
                    {studentSheetFiles.map((file) => (
                      <li key={file.name} className="flex items-center justify-between bg-gray-50 p-2 rounded-md">
                        <div className="flex items-center">
                          <FileText size={16} className="text-gray-500 mr-2" />
                          <span className="text-sm font-medium text-gray-700">{file.name}</span>
                        </div>
                        <button 
                          type="button" 
                          onClick={() => handleRemoveStudentFile(file.name)} 
                          className="text-red-500 hover:text-red-700"
                          title="Remove file"
                        >
                          <Trash2 size={16} />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <button type="submit" disabled={isLoading} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400">
              {isLoading ? 'İşleniyor...' : 'Değerlendir'}
            </button>

            {error && <div className="text-red-600 text-sm flex items-center"><XCircle className="h-4 w-4 mr-2"/> {error}</div>}
          </form>
        </div>
      </main>
    );
  }

  return (
    <main className="container mx-auto p-4 md:p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Değerlendirme Sonuçları</h1>
        <button onClick={() => setJobId(null)} className="text-sm text-indigo-600 hover:underline">Yeni Değerlendirme Başlat</button>
      </div>
      <p className="text-gray-600 mb-4">İşlem ID: <span className="font-mono text-xs">{jobId}</span></p>
      <ResultsDisplay events={events} />
    </main>
  );
}