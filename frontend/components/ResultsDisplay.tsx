'use client';

import { useState } from 'react';
import { Check, AlertCircle, Clock, PartyPopper, Send, Bot } from 'lucide-react';

// Tip Tanımlamaları
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


// --- YENİ: Her bir soru kartını ve kendi içindeki sohbet durumunu yöneten alt component ---
function QuestionResultCard({ result }: { result: GradingResultPayload }) {
  const [currentQuery, setCurrentQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'ai', content: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleFollowUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentQuery) return;
    
    setIsLoading(true);
    // Kullanıcının mesajını anında sohbete ekle
    setChatHistory(prev => [...prev, { role: 'user', content: currentQuery }]);
    const queryToSend = currentQuery;
    setCurrentQuery(''); // Input'u temizle

    try {
      const apiResponse = await fetch(`http://127.0.0.1:8000/api/followup/${result.job_id}/${result.student_id}/${result.question_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryToSend }),
      });
      if (!apiResponse.ok) throw new Error('API request failed');
      const data = await apiResponse.json();
      // AI'ın cevabını sohbete ekle
      setChatHistory(prev => [...prev, { role: 'ai', content: data.answer }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'ai', content: 'Soruya cevap alınamadı. Lütfen tekrar deneyin.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="border border-gray-400 p-4 rounded-md bg-gray-200">
      {/* Puanlama kısmı aynı */}
      <div className="flex justify-between items-center">
        <h3 className="font-bold text-lg text-gray-800">{result.question_id}</h3>
        <span className={`font-bold px-3 py-1 rounded-full text-sm ${result.score > result.max_score / 2 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          Points: {result.score} / {result.max_score}
        </span>
      </div>
      {result.friendly_feedback && <p className="mt-3 bg-blue-50 border-l-4 border-blue-400 p-3 text-sm text-gray-700">{result.friendly_feedback}</p>}
      
      {/* --- GÜNCELLENMİŞ SOHBET BÖLÜMÜ --- */}
      <div className="mt-4 space-y-3">
        {/* Sohbet Geçmişi */}
        {chatHistory.map((msg, index) => (
          <div key={index} className={`flex items-start gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'ai' && <div className="bg-indigo-600 text-white p-2 rounded-full flex-shrink-0"><Bot size={16} /></div>}
            <div className={`p-3 rounded-lg max-w-xs ${msg.role === 'ai' ? 'bg-black text-white' : 'bg-blue-500 text-white'}`}>
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}
        {isLoading && <p className="text-sm text-gray-500 mt-2 flex items-center"><Clock size={14} className="animate-spin mr-1"/> AI is thinking...</p>}

        {/* Soru Sorma Formu */}
        <form onSubmit={handleFollowUp} className="flex items-center space-x-2 pt-2">
          <input type="text" value={currentQuery} onChange={(e) => setCurrentQuery(e.target.value)} placeholder="Ask a follow-up question..." className="flex-grow p-2 border border-gray-300 rounded-md text-sm bg-black text-white" disabled={isLoading} />
          <button type="submit" className="bg-black text-white p-2 rounded-md hover:bg-gray-800 disabled:bg-gray-400" disabled={isLoading}><Send size={18} /></button>
        </form>
      </div>
      
      {/* Teknik Detaylar kısmı aynı */}
      <details className="mt-3">
        <summary className="cursor-pointer text-xs text-yellow-700">Show Technical Details</summary>
        <div className="mt-2 p-3 rounded text-xs text-gray-600 space-y-2">
          <p><strong>Justification:</strong> {result.justification}</p>
          {result.verifier_status.valid ? (<p className="text-green-600 flex items-center"><Check size={14} className="mr-1"/> Verification Successful</p>) 
          : (<p className="text-red-600 flex items-center"><AlertCircle size={14} className="mr-1"/> Verification Error: {result.verifier_status.issues.join(', ')}</p>)}
        </div>
      </details>
    </div>
  );
}


// Ana Display Component'i
export default function ResultsDisplay({ events }: { events: StreamEvent[] }) {
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
            <p className="font-bold">An Error Occurred</p>
            <p>{(errorEvent.payload as ErrorPayload).message}</p>
        </div>
    );
  }

  return (
    <div className="space-y-8">
      {studentOrder.map(studentId => {
        const studentResults = resultsByStudent[studentId] || [];
        const processedCount = studentResults.length;
        const progressPercentage = totalQuestions > 0 ? (processedCount / totalQuestions) * 100 : 0;
        const isStudentDone = summaries.some(s => s.student_id === studentId);
        const studentSummary = summaries.find(s => s.student_id === studentId);

        return (
          <div key={studentId} className="bg-white p-6 rounded-lg shadow">
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <h2 className="text-xl font-semibold text-gray-800">Student: {studentId}</h2>
                {isStudentDone ? (<span className="text-green-600 flex items-center font-medium"><Check size={18} className="mr-1"/> Completed</span>) 
                : (<span className="text-blue-600 flex items-center font-medium"><Clock size={16} className="mr-1 animate-spin"/> In Progress...</span>)}
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div className={`h-2.5 rounded-full transition-all duration-500 ${isStudentDone ? 'bg-green-500' : 'bg-blue-600'}`} style={{ width: `${progressPercentage}%` }}></div>
              </div>
              {!isStudentDone && (<div className="text-right text-sm text-gray-500 mt-1">{processedCount} / {totalQuestions} Questions</div>)}
            </div>
            
            <div className="space-y-4 border-t border-gray-200 pt-4">
              {studentResults.map(res => (<QuestionResultCard key={res.question_id} result={res} />))}
            </div>

            {studentSummary && (
               <div className="mt-6 bg-green-50 border-l-4 border-green-500 p-4 rounded">
                  <h3 className="font-bold mb-2 text-black">Student Summary</h3>
                  <div className="prose prose-sm max-w-none text-gray-700" dangerouslySetInnerHTML={{ __html: studentSummary.summary_report.replace(/\n/g, '<br />') }} />
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