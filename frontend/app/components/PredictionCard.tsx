'use client';

import React, { useState } from 'react';
import { MatchPrediction } from '@/app/services/api';

interface PredictionCardProps {
  prediction: MatchPrediction;
  onAnalyze?: (matchId: number) => void;
}

export default function PredictionCard({ prediction, onAnalyze }: PredictionCardProps) {
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const handleAnalyze = async () => {
    if (onAnalyze) {
      onAnalyze(prediction.match_id);
    }
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-700 p-6 hover:border-gray-500 transition-all duration-300">
      {/* Header - Clickable */}
      <div 
        className="cursor-pointer"
        onClick={handleAnalyze}
      >
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-xl font-bold text-white hover:text-blue-400 transition-colors">
              {prediction.home_team} vs {prediction.away_team}
              <span className="text-xs text-blue-400 ml-2">📊 Click for Analysis</span>
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-gray-400 text-sm bg-gray-800 px-2 py-0.5 rounded">
                {prediction.league}
              </span>
              <span className="text-gray-500 text-sm">
                Match #{prediction.match_id}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">Confidence</div>
            <div className={`text-lg font-bold ${
              prediction.confidence_score > 0.4 ? 'text-green-400' : 
              prediction.confidence_score > 0.25 ? 'text-yellow-400' : 'text-gray-400'
            }`}>
              {formatPercentage(prediction.confidence_score)}
            </div>
          </div>
        </div>
      </div>

      {/* Rest of the card content (same as before) */}
      {/* Expected Goals */}
      <div className="grid grid-cols-2 gap-4 mb-4 bg-gray-800 rounded-lg p-3">
        <div className="text-center">
          <div className="text-xs text-gray-500">Expected Goals</div>
          <div className="text-white font-bold">
            {prediction.expected_home_goals.toFixed(2)}
          </div>
          <div className="text-sm text-green-400">{prediction.home_team}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500">Expected Goals</div>
          <div className="text-white font-bold">
            {prediction.expected_away_goals.toFixed(2)}
          </div>
          <div className="text-sm text-red-400">{prediction.away_team}</div>
        </div>
      </div>

      {/* 1X2 Probabilities */}
      <div className="space-y-2 mb-4">
        <div>
          <div className="flex justify-between text-sm">
            <span className="text-green-400">Home Win</span>
            <span className="text-white font-medium">
              {formatPercentage(prediction.home_win)}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${prediction.home_win * 100}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-sm">
            <span className="text-yellow-400">Draw</span>
            <span className="text-white font-medium">
              {formatPercentage(prediction.draw)}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-yellow-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${prediction.draw * 100}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-sm">
            <span className="text-red-400">Away Win</span>
            <span className="text-white font-medium">
              {formatPercentage(prediction.away_win)}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-red-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${prediction.away_win * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Over/Under */}
      <div className="flex items-center justify-between bg-gray-800 rounded-lg p-3 mb-4">
        <span className="text-gray-300">Over/Under 2.5 Goals</span>
        <div className="flex gap-4">
          <span className="text-blue-400">
            Over {formatPercentage(prediction.over_25)}
          </span>
          <span className="text-gray-400">|</span>
          <span className="text-orange-400">
            Under {formatPercentage(prediction.under_25)}
          </span>
        </div>
      </div>

      {/* Most Likely Scores */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-400 mb-2">Most Likely Scores</h4>
        <div className="grid grid-cols-3 gap-2">
          {prediction.most_likely_scores.slice(0, 3).map((score, index) => (
            <div key={index} className="text-center bg-gray-800 rounded-lg p-2">
              <div className="text-white font-bold">{score.score}</div>
              <div className="text-xs text-gray-400">
                {formatPercentage(score.probability)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}