'use client';

import { useState, useEffect, useRef } from 'react';
import { PredictionAPI, MatchPrediction } from '@/app/services/api';
import PredictionCard from '@/app/components/PredictionCard';
import NewsFeed from '@/app/components/NewsFeed';
import AccuracyDashboard from '@/app/components/AccuracyDashboard';

export default function HomePage() {
  const [matches, setMatches] = useState<MatchPrediction[]>([]);
  const [liveMatches, setLiveMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'predictions' | 'live' | 'news' | 'accuracy'>('predictions');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchPredictions();
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const wsUrl = 'ws://127.0.0.1:8000/ws/live';
      console.log('Connecting to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'initial' || data.type === 'live_update') {
            setLiveMatches(data.matches || []);
            console.log(`📊 Received ${data.matches?.length || 0} live matches`);
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };
      
      ws.onerror = () => {
        console.log('WebSocket not available (normal if no live matches)');
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...');
        setTimeout(connectWebSocket, 5000);
      };
      
      wsRef.current = ws;
    } catch (e) {
      console.log('WebSocket not available (normal)');
    }
  };

  const fetchPredictions = async () => {
    setLoading(true);
    setError(null);
    try {
      const predictions = await Promise.all(
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(async (id) => {
          try {
            return await PredictionAPI.getMatchPrediction(id);
          } catch {
            return null;
          }
        })
      );
      const valid = predictions.filter((p): p is MatchPrediction => p !== null);
      setMatches(valid);
    } catch (err) {
      setError('Failed to load predictions.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (matchId: number) => {
    setSelectedMatch(matchId);
    setAnalysisLoading(true);
    setAnalysis(null);
    try {
      const result = await PredictionAPI.getMatchAnalysis(matchId);
      setAnalysis(result);
    } catch (err) {
      console.error('Failed to load analysis:', err);
    } finally {
      setAnalysisLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-900/50 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
                ⚽ AI Prediction Engine
              </h1>
              <p className="text-gray-400 text-sm hidden sm:block">
                Meta-prediction platform for Top 5 European Leagues
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500 bg-gray-800 px-3 py-1 rounded-full">
                {liveMatches.length} Live Matches
              </span>
              <button
                onClick={fetchPredictions}
                className="text-sm bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
              >
                🔄 Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="container mx-auto px-4 py-4">
        <div className="flex flex-wrap gap-2 border-b border-gray-700">
          <button
            onClick={() => setActiveTab('predictions')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'predictions'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            📊 Predictions
          </button>
          <button
            onClick={() => setActiveTab('live')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'live'
                ? 'text-green-400 border-b-2 border-green-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            🔴 Live {liveMatches.length > 0 && `(${liveMatches.length})`}
          </button>
          <button
            onClick={() => setActiveTab('news')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'news'
                ? 'text-yellow-400 border-b-2 border-yellow-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            📰 News
          </button>
          <button
            onClick={() => setActiveTab('accuracy')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'accuracy'
                ? 'text-purple-400 border-b-2 border-purple-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            📊 Accuracy
          </button>
        </div>
      </div>

      {/* Analysis Modal */}
      {analysis && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 rounded-xl border border-gray-700 max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-2xl font-bold text-white">
                {analysis.match_info?.home_team || 'Unknown'} vs {analysis.match_info?.away_team || 'Unknown'}
              </h2>
              <button
                onClick={() => setAnalysis(null)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 mb-4">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">📊 Analysis Summary</h3>
              <p className="text-gray-300">{analysis.summary || 'No summary available'}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-yellow-400 mb-2">⚡ Elo Rating</h4>
                <p className="text-gray-300 text-sm">{analysis.factors?.elo?.text || 'N/A'}</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-green-400 mb-2">📈 Form</h4>
                <p className="text-gray-300 text-sm">{analysis.factors?.form?.text || 'N/A'}</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-purple-400 mb-2">📋 Head-to-Head</h4>
                <p className="text-gray-300 text-sm">{analysis.factors?.h2h?.summary || 'N/A'}</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-red-400 mb-2">🏥 Injuries</h4>
                <p className="text-gray-300 text-sm">{analysis.factors?.injuries?.text || 'N/A'}</p>
              </div>
            </div>

            {analysis.key_battles && analysis.key_battles.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <h3 className="text-lg font-semibold text-orange-400 mb-2">⚔️ Key Battles</h3>
                <ul className="text-gray-300 text-sm space-y-1">
                  {analysis.key_battles.map((battle: string, i: number) => (
                    <li key={i}>• {battle}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-400 mb-2">🔮 Prediction</h4>
                <p className="text-gray-300 text-sm">{analysis.prediction_text || 'N/A'}</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-green-400 mb-2">💰 Betting Insight</h4>
                <p className="text-gray-300 text-sm">{analysis.betting_insight || 'N/A'}</p>
              </div>
            </div>

            <button
              onClick={() => setAnalysis(null)}
              className="mt-6 w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
            >
              Close Analysis
            </button>
          </div>
        </div>
      )}

      {analysisLoading && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading AI analysis...</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {loading && (
          <div className="flex justify-center items-center h-64">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-400">Loading predictions...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-500 rounded-lg p-6 text-center">
            <p className="text-red-400">❌ {error}</p>
            <button
              onClick={fetchPredictions}
              className="mt-4 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && activeTab === 'predictions' && matches.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            No predictions available
          </div>
        )}

        {!loading && !error && activeTab === 'predictions' && matches.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {matches.map((match) => (
              <PredictionCard 
                key={match.match_id} 
                prediction={match} 
                onAnalyze={handleAnalyze}
              />
            ))}
          </div>
        )}

        {activeTab === 'live' && (
          <div>
            {liveMatches.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                No live matches at the moment
                <p className="text-sm mt-2 text-gray-500">
                  WebSocket is connected but no matches are currently live
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {liveMatches.slice(0, 20).map((match: any) => {
                  const home = match.teams?.home?.name || 'Unknown';
                  const away = match.teams?.away?.name || 'Unknown';
                  const homeScore = match.goals?.home ?? '-';
                  const awayScore = match.goals?.away ?? '-';
                  const status = match.fixture?.status?.short || 'NS';
                  const elapsed = match.fixture?.status?.elapsed || 0;

                  return (
                    <div key={match.fixture?.id} className="bg-gray-900 rounded-xl border border-green-700 p-6 hover:border-green-500 transition-all duration-300">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-xl font-bold text-white">
                            {home} vs {away}
                          </h3>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-green-400 text-sm bg-green-900/30 px-2 py-0.5 rounded">
                              🔴 LIVE {elapsed}' 
                            </span>
                            <span className="text-gray-500 text-sm">
                              {status}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-white">
                            {homeScore} - {awayScore}
                          </div>
                        </div>
                      </div>
                      <div className="bg-gray-800 rounded-lg p-3 text-center text-gray-400 text-sm">
                        Live match in progress
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'news' && <NewsFeed />}
        {activeTab === 'accuracy' && <AccuracyDashboard />}
      </main>

      <footer className="border-t border-gray-800 bg-gray-900/50 py-4 mt-8">
        <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
          ⚽ AI Football Prediction Engine • For informational purposes only
        </div>
      </footer>
    </div>
  );
}