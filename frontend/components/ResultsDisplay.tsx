'use client';

import { Check, AlertCircle, Clock, PartyPopper } from 'lucide-react';

// Backend'den gelen veri yapılarına uygun TypeScript tipleri
interface GradingResult {
  job_id: string;
  student_id: string;
  question_id: string;
  score: number;
  max_score: number;
  justification: string;
  friendly_feedback?: string;
  verifier_status: {
    valid: boolean;
    issues: string[];
  };
}

interface StudentSummary {
  student_id: string;
  summary_report: string;
}

export interface StreamEvent {
  type: 'partial_result' | 'student_summary' | 'job_done' | 'error';
  payload: GradingResult | StudentSummary; // GradingResult veya StudentSummary olabilir
  timestamp: string;
}

// Ana component
export default function ResultsDisplay({ events }: { events: StreamEvent[] }) {
  const partialResults = events.filter(e => e.type === 'partial_result');
  const summaries = events.filter(e => e.type === 'student_summary');
  const isDone = events.some(e => e.type === 'job_done');

  // Sonuçları öğrenci ID'sine göre gruplayalım
  const resultsByStudent = partialResults.reduce((acc, event) => {
    const result = event.payload as GradingResult;
    if (!acc[result.student_id]) {
      acc[result.student_id] = [];
    }
    acc[result.student_id].push(result);
    return acc;
  }, {} as Record<string, GradingResult[]>);

  return (
    <div className="space-y-8">
      {Object.keys(resultsByStudent).map(studentId => (
        <div key={studentId} className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Öğrenci: {studentId}</h2>
          <div className="space-y-4">
            {resultsByStudent[studentId].map(res => (
              <div key={res.question_id} className="border border-gray-200 p-4 rounded-md">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-lg">{res.question_id}</h3>
                  <span className={`font-bold px-3 py-1 rounded-full text-sm ${
                    res.score > res.max_score / 2 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    Puan: {res.score} / {res.max_score}
                  </span>
                </div>

                {res.friendly_feedback && (
                   <p className="mt-3 bg-blue-50 border-l-4 border-blue-400 p-3 text-gray-700">
                    {res.friendly_feedback}
                   </p>
                )}

                <details className="mt-3">
                  <summary className="cursor-pointer text-sm text-gray-500">Teknik Detayları Göster</summary>
                  <div className="mt-2 bg-gray-50 p-3 rounded text-xs text-gray-600 space-y-2">
                    <p><strong>Gerekçe:</strong> {res.justification}</p>
                    {res.verifier_status.valid ? (
                      <p className="text-green-600 flex items-center"><Check size={14} className="mr-1"/> Doğrulama Başarılı</p>
                    ) : (
                      <p className="text-red-600 flex items-center"><AlertCircle size={14} className="mr-1"/> Doğrulama Hatası: {res.verifier_status.issues.join(', ')}</p>
                    )}
                  </div>
                </details>
              </div>
            ))}
          </div>
          {summaries.find(s => s.payload.student_id === studentId) && (
             <div className="mt-6 bg-green-50 border-l-4 border-green-500 p-4 rounded">
                <h3 className="font-bold mb-2">Öğrenci Özeti</h3>
                <div className="prose prose-sm max-w-none" 
                    dangerouslySetInnerHTML={{ __html: (summaries.find(s => s.payload.student_id === studentId)?.payload as StudentSummary).summary_report.replace(/\n/g, '<br />') }} />
             </div>
          )}
        </div>
      ))}
       {!isDone && Object.keys(resultsByStudent).length > 0 && (
        <div className="flex items-center justify-center text-gray-500 mt-8">
            <Clock size={18} className="mr-2 animate-spin"/>
            <span>Değerlendirme devam ediyor...</span>
        </div>
       )}
      {isDone && (
        <div className="flex items-center justify-center text-green-600 font-bold mt-8 bg-green-100 p-4 rounded-lg">
            <PartyPopper size={24} className="mr-3"/>
            <span>Tüm değerlendirmeler tamamlandı!</span>
        </div>
      )}
    </div>
  );
}