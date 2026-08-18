'use client';

import { useState, useEffect } from 'react';
import { PredictionAPI } from '@/app/services/api';

interface Fixture {
  id: number;
  home_team: string;
  away_team: string;
  match_date: string;
  venue: string;
  status: string;
  home_score: number | null;
  away_score: number | null;
  has_prediction: boolean;
  prediction_available: boolean;
}

interface League {
  id: number;
  name: string;
  country: string;
  api_id: number;
}

export default function LeagueFixtures() {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<number | null>(null);
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMatch, setSelectedMatch] = useState<Fixture | null>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [predictionLoading, setPredictionLoading] = useState(false);

  useEffect(() => {
    fetchLeagues();
  }, []);

  useEffect(() => {
    if (selectedLeague) {
      fetchFixtures(selectedLeague);
    }
  }, [selectedLeague]);

  const fetchLeagues = async () => {
    try {
      const data = await PredictionAPI.getLeagues();
      setLeagues(data);
      if (data.length > 0) {
        setSelectedLeague(data[0].id);
      }
    } catch (error) {
      console.error('Error fetching leagues:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFixtures = async (leagueId: number) => {
    setLoading(true);
    try {
      const data = await PredictionAPI.getFixtures(leagueId);
      setFixtures(data.fixtures || []);
    } catch (error) {
      console.error('Error fetching fixtures:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPrediction = async (matchId: number) => {
    setPredictionLoading(true);
    try {
      const data = await PredictionAPI.getMatchPrediction(matchId);
      setPrediction(data);
    } catch (error) {
      console.error('Error fetching prediction:', error);
      setPrediction(null);
    } finally {
      setPredictionLoading(false);
    }
  };

  const handleMatchClick = (fixture: Fixture) => {
    setSelectedMatch(fixture);
    if (fixture.prediction_available) {
      fetchPrediction(fixture.id);
    } else {
      setPrediction(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isPredictionAvailable = (fixture: Fixture) => {
    const matchTime = new Date(fixture.match_date).getTime();
    const now = new Date().getTime();
    const hoursUntilMatch = (matchTime - now) / (1000 * 60 * 60);
    return hoursUntilMatch <= 4 && hoursUntilMatch > 0;
  };

  if (loading && leagues.length === 0) {
    return <div className="text-gray-400">Loading leagues...</div>;
  }

  return (
    <div>
      {/* League Buttons */}
      <div className="flex flex-wrap gap-2 mb-6">
        {leagues.map((league) => (
          <button
            key={league.id}
            onClick={() => setSelectedLeague(league.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedLeague === league.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {league.name}
          </button>
        ))}
      </div>

      {/* Fixtures List */}
      <div className="space-y-3">
        {fixtures.length === 0 ? (
          <p className="text-gray-400">No fixtures available for this league.</p>
        ) : (
          fixtures.map((fixture) => {
            const predictionAvailable = isPredictionAvailable(fixture);
            const isSelected = selectedMatch?.id === fixture.id;

            return (
              <div
                key={fixture.id}
                onClick={() => handleMatchClick(fixture)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-gray-800 border-blue-500'
                    : 'bg-gray-900 border-gray-700 hover:border-gray-500'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-white font-medium">
                      {fixture.home_team} vs {fixture.away_team}
                    </div>
                    <div className="text-gray-400 text-sm">
                      {fixture.venue} • {formatDate(fixture.match_date)}
                    </div>
                  </div>
                  <div className="text-right">
                    {fixture.status === 'FT' ? (
                      <span className="text-white font-bold">
                        {fixture.home_score} - {fixture.away_score}
                      </span>
                    ) : predictionAvailable ? (
                      <span className="text-green-400 text-sm">🔮 Prediction Available</span>
                    ) : (
                      <span className="text-yellow-400 text-sm">
                        ⏳ {Math.ceil((new Date(fixture.match_date).getTime() - new Date().getTime()) / (1000 * 60 * 60))}h
                      </span>
                    )}
                  </div>
                </div>

                {/* Prediction Display */}
                {isSelected && predictionLoading && (
                  <div className="mt-4 text-gray-400">Loading prediction...</div>
                )}

                {isSelected && !predictionLoading && prediction && (
                  <div className="mt-4 p-4 bg-gray-800 rounded-lg border border-blue-500">
                    <h4 className="text-sm font-semibold text-blue-400 mb-3">📊 Prediction</h4>
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-sm">
                          <span className="text-green-400">Home Win</span>
                          <span>{(prediction.home_win * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-green-500 h-1.5 rounded-full"
                            style={{ width: `${prediction.home_win * 100}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm">
                          <span className="text-yellow-400">Draw</span>
                          <span>{(prediction.draw * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-yellow-500 h-1.5 rounded-full"
                            style={{ width: `${prediction.draw * 100}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm">
                          <span className="text-red-400">Away Win</span>
                          <span>{(prediction.away_win * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-red-500 h-1.5 rounded-full"
                            style={{ width: `${prediction.away_win * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="text-xs text-gray-400 mt-2">
                        Confidence: {(prediction.confidence_score * 100).toFixed(1)}%
                      </div>
                    </div>'use client';

import { useState, useEffect } from 'react';
import { PredictionAPI } from '@/app/services/api';

interface Fixture {
  id: number;
  home_team: string;
  away_team: string;
  match_date: string;
  venue: string;
  status: string;
  home_score: number | null;
  away_score: number | null;
  has_prediction: boolean;
  prediction_available: boolean;
}

interface League {
  id: number;
  name: string;
  country: string;
  api_id: number;
}

export default function LeagueFixtures() {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<number | null>(null);
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMatch, setSelectedMatch] = useState<Fixture | null>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [predictionLoading, setPredictionLoading] = useState(false);

  useEffect(() => {
    fetchLeagues();
  }, []);

  useEffect(() => {
    if (selectedLeague) {
      fetchFixtures(selectedLeague);
    }
  }, [selectedLeague]);

  const fetchLeagues = async () => {
    try {
      const data = await PredictionAPI.getLeagues();
      setLeagues(data);
      if (data.length > 0) {
        setSelectedLeague(data[0].id);
      }
    } catch (error) {
      console.error('Error fetching leagues:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFixtures = async (leagueId: number) => {
    setLoading(true);
    try {
      const data = await PredictionAPI.getFixtures(leagueId);
      setFixtures(data.fixtures || []);
    } catch (error) {
      console.error('Error fetching fixtures:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPrediction = async (matchId: number) => {
    setPredictionLoading(true);
    try {
      const data = await PredictionAPI.getMatchPrediction(matchId);
      setPrediction(data);
    } catch (error) {
      console.error('Error fetching prediction:', error);
      setPrediction(null);
    } finally {
      setPredictionLoading(false);
    }
  };

  const handleMatchClick = (fixture: Fixture) => {
    setSelectedMatch(fixture);
    if (fixture.prediction_available) {
      fetchPrediction(fixture.id);
    } else {
      setPrediction(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isPredictionAvailable = (fixture: Fixture) => {
    const matchTime = new Date(fixture.match_date).getTime();
    const now = new Date().getTime();
    const hoursUntilMatch = (matchTime - now) / (1000 * 60 * 60);
    return hoursUntilMatch <= 4 && hoursUntilMatch > 0;
  };

  if (loading && leagues.length === 0) {
    return <div className="text-gray-400">Loading leagues...</div>;
  }

  return (
    <div>
      {/* League Buttons */}
      <div className="flex flex-wrap gap-2 mb-6">
        {leagues.map((league) => (
          <button
            key={league.id}
            onClick={() => setSelectedLeague(league.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedLeague === league.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {league.name}
          </button>
        ))}
      </div>

      {/* Fixtures List */}
      <div className="space-y-3">
        {loading && fixtures.length === 0 ? (
          <div className="text-gray-400">Loading fixtures...</div>
        ) : fixtures.length === 0 ? (
          <p className="text-gray-400">No fixtures available for this league.</p>
        ) : (
          fixtures.map((fixture) => {
            const predictionAvailable = isPredictionAvailable(fixture);
            const isSelected = selectedMatch?.id === fixture.id;

            return (
              <div
                key={fixture.id}
                onClick={() => handleMatchClick(fixture)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-gray-800 border-blue-500'
                    : 'bg-gray-900 border-gray-700 hover:border-gray-500'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-white font-medium">
                      {fixture.home_team} vs {fixture.away_team}
                    </div>
                    <div className="text-gray-400 text-sm">
                      {fixture.venue} • {formatDate(fixture.match_date)}
                    </div>
                  </div>
                  <div className="text-right">
                    {fixture.status === 'FT' ? (
                      <span className="text-white font-bold">
                        {fixture.home_score} - {fixture.away_score}
                      </span>
                    ) : predictionAvailable ? (
                      <span className="text-green-400 text-sm">🔮 Prediction Available</span>
                    ) : fixture.status === 'NS' ? (
                      <span className="text-yellow-400 text-sm">
                        ⏳ {Math.ceil((new Date(fixture.match_date).getTime() - new Date().getTime()) / (1000 * 60 * 60))}h
                      </span>
                    ) : (
                      <span className="text-gray-500 text-sm">{fixture.status}</span>
                    )}
                  </div>
                </div>

                {/* Prediction Display */}
                {isSelected && predictionLoading && (
                  <div className="mt-4 text-gray-400">Loading prediction...</div>
                )}

                {isSelected && !predictionLoading && prediction && (
                  <div className="mt-4 p-4 bg-gray-800 rounded-lg border border-blue-500">
                    <h4 className="text-sm font-semibold text-blue-400 mb-3">🔮 Prediction</h4>
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-sm">
                          <span className="text-green-400">Home Win</span>
                          <span className="text-white">{(prediction.home_win * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-green-500 h-1.5 rounded-full"
                            style={{ width: `${prediction.home_win * 100}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm">
                          <span className="text-yellow-400">Draw</span>
                          <span className="text-white">{(prediction.draw * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-yellow-500 h-1.5 rounded-full"
                            style={{ width: `${prediction.draw * 100}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm">
                          <span className="text-red-400">Away Win</span>
                          <span className="text-white">{(prediction.away_win * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-red-500 h-1.5 rounded-full"
                            style={{ width: `${prediction.away_win * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="flex justify-between text-xs text-gray-400 mt-2">
                        <span>Confidence: {(prediction.confidence_score * 100).toFixed(1)}%</span>
                        <span>Over 2.5: {(prediction.over_25 * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                )}

                {isSelected && !predictionLoading && !prediction && fixture.status === 'NS' && (
                  <div className="mt-4 text-yellow-400 text-sm">
                    ⏳ Prediction available 4-2 hours before kickoff
                  </div>
                )}

                {isSelected && !predictionLoading && !prediction && fixture.status === 'FT' && (
                  <div className="mt-4 text-gray-400 text-sm">
                    Match has finished. Check predictions tab for accuracy.
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
                  </div>
                )}

                {isSelected && !predictionLoading && !prediction && (
                  <div className="mt-4 text-yellow-400 text-sm">
                    ⏳ Prediction available 4-2 hours before kickoff
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}