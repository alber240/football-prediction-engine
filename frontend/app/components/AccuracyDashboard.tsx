'use client';

import { useState, useEffect } from 'react';
import { PredictionAPI } from '@/app/services/api';

interface AccuracyData {
  date: string;
  total_predictions: number;
  correct_predictions: number;
  accuracy_percentage: number;
  results: Array<{
    match_id: number;
    home_team: string;
    away_team: string;
    actual_score: string;
    correct: boolean;
  }>;
}

export default function AccuracyDashboard() {
  const [accuracy, setAccuracy] = useState<AccuracyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [selectedLeague, setSelectedLeague] = useState<string>('all');

  useEffect(() => {
    fetchAccuracy();
  }, [selectedDate, selectedLeague]);

  const fetchAccuracy = async () => {
    setLoading(true);
    try {
      // For now, fetch daily accuracy
      const data = await PredictionAPI.getDailyAccuracy(selectedDate);
      setAccuracy(data);
    } catch (error) {
      console.error('Error fetching accuracy:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-gray-400">Loading accuracy...</div>;

  if (!accuracy || accuracy.total_predictions === 0) {
    return (
      <div className="bg-gray-900 rounded-xl border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">📊 Daily Accuracy</h2>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-1"
          />
        </div>
        <p className="text-gray-400">No predictions available for this date.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">📊 Daily Accuracy</h2>
        <div className="flex gap-2">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-1 text-sm"
          />
          <button
            onClick={fetchAccuracy}
            className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-gray-400 text-sm">Total Predictions</div>
          <div className="text-2xl font-bold text-white">{accuracy.total_predictions}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-gray-400 text-sm">Correct</div>
          <div className="text-2xl font-bold text-green-400">{accuracy.correct_predictions}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-gray-400 text-sm">Accuracy</div>
          <div className={`text-2xl font-bold ${
            accuracy.accuracy_percentage > 60 ? 'text-green-400' :
            accuracy.accuracy_percentage > 40 ? 'text-yellow-400' :
            'text-red-400'
          }`}>
            {accuracy.accuracy_percentage}%
          </div>
        </div>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        <div className="flex justify-between items-center text-gray-400 text-sm px-3 py-1 border-b border-gray-700">
          <span>Match</span>
          <span>Result</span>
          <span>Status</span>
        </div>
        {accuracy.results.map((result) => (
          <div
            key={result.match_id}
            className={`flex items-center justify-between p-3 rounded-lg ${
              result.correct ? 'bg-green-900/20 border border-green-700' : 'bg-red-900/20 border border-red-700'
            }`}
          >
            <div className="flex-1">
              <span className="text-white text-sm">
                {result.home_team} vs {result.away_team}
              </span>
              <span className="text-gray-400 text-xs ml-2">
                {result.actual_score}
              </span>
            </div>
            <div>
              {result.correct ? (
                <span className="text-green-400 text-sm">✅ Correct</span>
              ) : (
                <span className="text-red-400 text-sm">❌ Incorrect</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 text-center text-xs text-gray-500">
        {accuracy.total_predictions > 0 && 
          `Last updated: ${new Date().toLocaleString()}`
        }
      </div>
    </div>
  );
}