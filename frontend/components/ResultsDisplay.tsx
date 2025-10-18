'use client';

import { Check, AlertCircle, Clock, PartyPopper } from 'lucide-react';

// Tip tanımlamaları aynı kalıyor
interface GradingResultPayload {
  job_id: string;
  student_id: string;
  question_id: string;
  score: number;
  max_score: number;
  justification: string;
  friendly_feedback?: string;
  verifier_status: { valid: boolean; issues: string[]; };
}
interface JobStartedPayload { total_questions: number; }
interface StudentSummaryPayload { student_id: string; summary_report: string; }
interface JobDonePayload { job_id: string; }
interface ErrorPayload { message: string; }
type StreamEventPayload = GradingResultPayload | JobStartedPayload | StudentSummaryPayload | JobDonePayload | ErrorPayload;
export interface StreamEvent {
  type: 'job_started' | 'partial_result' | 'student_summary' | 'job_done' | 'error';
  payload: StreamEventPayload;
  timestamp: string;
}

export default function ResultsDisplay({ events }: { events: StreamEvent[] }) {
  // Veri hazırlama adımları aynı
  const jobStartedEvent = events.find(e => e.type === 'job_started');
  const totalQuestions = jobStartedEvent ? (jobStartedEvent.payload as JobStartedPayload).total_questions : 0;
  const partialResults = events.filter(e => e.type === 'partial_result').map(e => e.payload as GradingResultPayload);
  const summaries = events.filter(e => e.type === 'student_summary').map(e => e.payload as StudentSummaryPayload);
  const isDone = events.some(e => e.type === 'job_done');
  const errorEvent = events.find(e => e.type === 'error');

  const resultsByStudent = partialResults.reduce((acc, result) => {
    if (!acc[result.student_id]) acc[result.student_id] = [];
    acc[result.student_id].push(result);
    return acc;
  }, {} as Record<string, GradingResultPayload[]>);
  
  const studentOrder = Object.keys(resultsByStudent);

  if (errorEvent) {
    return (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-lg shadow" role="alert">
            <p className="font-bold">Bir Hata Oluştu</p>
            <p>{(errorEvent.payload as ErrorPayload).message}</p>
        </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* --- YENİ YAPI: Her öğrenci için tek bir ana döngü --- */}
      {studentOrder.map(studentId => {
        const studentResults = resultsByStudent[studentId] || [];
        const processedCount = studentResults.length;
        const progressPercentage = totalQuestions > 0 ? (processedCount / totalQuestions) * 100 : 0;
        const isStudentDone = summaries.some(s => s.student_id === studentId);
        const studentSummary = summaries.find(s => s.student_id === studentId);

        return (
          <div key={studentId} className="bg-white p-6 rounded-lg shadow">
            {/* --- 1. Başlık ve İlerleme Çubuğu Bölümü --- */}
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <h2 className="text-xl font-semibold text-gray-800">Öğrenci: {studentId}</h2>
                {isStudentDone ? (
                  <span className="text-green-600 flex items-center font-medium"><Check size={18} className="mr-1"/> Completed</span>
                ) : (
                  <span className="text-blue-600 flex items-center font-medium"><Clock size={16} className="mr-1 animate-spin"/> In Progress...</span>
                )}
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className={`h-2.5 rounded-full transition-all duration-500 ${isStudentDone ? 'bg-green-500' : 'bg-blue-600'}`}
                  style={{ width: `${progressPercentage}%` }}>
                </div>
              </div>
              {!isStudentDone && (
                <div className="text-right text-sm text-gray-500 mt-1">
                  {processedCount} / {totalQuestions} Questions
                </div>
              )}
            </div>

            {/* --- 2. Soru Sonuçları Bölümü (Anlık olarak dolacak) --- */}
            <div className="space-y-4 border-t border-gray-200 pt-4">
              {studentResults.map(res => (
                <div key={res.question_id} className="border border-gray-400 p-4 rounded-md bg-gray-200">
                  <div className="flex justify-between items-center">
                    <h3 className="font-bold text-lg text-gray-800">{res.question_id}</h3>
                    <span className={`font-bold px-3 py-1 rounded-full text-sm ${res.score > res.max_score / 2 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      Points: {res.score} / {res.max_score}
                    </span>
                  </div>
                  {res.friendly_feedback && (
                     <p className="mt-3 bg-blue-50 border-l-4 border-blue-400 p-3 text-sm text-gray-700">{res.friendly_feedback}</p>
                  )}
                  <details className="mt-3">
                    <summary className="cursor-pointer text-xs text-yellow-700">Show Technical Details</summary>
                    <div className="mt-2 p-3 rounded text-xs text-gray-600 space-y-2">
                      <p><strong>Justification:</strong> {res.justification}</p>
                      {res.verifier_status.valid ? (
                        <p className="text-green-600 flex items-center"><Check size={14} className="mr-1"/> Verification Successful</p>
                      ) : (
                        <p className="text-red-600 flex items-center"><AlertCircle size={14} className="mr-1"/> Verification Error: {res.verifier_status.issues.join(', ')}</p>
                      )}
                    </div>
                  </details>
                </div>
              ))}
            </div>
            
            {/* --- 3. Öğrenci Özeti Bölümü (İş bitince görünecek) --- */}
            {studentSummary && (
               <div className="mt-6 bg-green-50 border-l-4 border-green-500 p-4 rounded">
                  <h3 className="font-bold mb-2 text-black">Student Summary</h3>
                  <div className="prose prose-sm max-w-none text-gray-700" 
                      dangerouslySetInnerHTML={{ __html: studentSummary.summary_report.replace(/\n/g, '<br />') }} />
               </div>
            )}
          </div>
        )
      })}
      
      {isDone && (
        <div className="flex items-center justify-center text-green-600 font-bold mt-8 bg-green-100 p-4 rounded-lg">
            <PartyPopper size={24} className="mr-3"/>
            <span>All evaluations are complete!</span>
        </div>
      )}
    </div>
  );
}