// app/services/api.ts
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface ScoreProbability {
  score: string;
  probability: number;
}

export interface MatchPrediction {
  match_id: number;
  home_team: string;
  away_team: string;
  league: string;
  expected_home_goals: number;
  expected_away_goals: number;
  home_win: number;
  draw: number;
  away_win: number;
  over_25: number;
  under_25: number;
  most_likely_scores: ScoreProbability[];
  confidence_score: number;
  prediction_time: string;
}

export interface MatchAnalysis {
  match_info: {
    home_team: string;
    away_team: string;
    match_id: number;
    venue: string;
  };
  factors: {
    elo: any;
    form: any;
    h2h: any;
    injuries: any;
  };
  summary: string;
  key_battles: string[];
  prediction_text: string;
  betting_insight: string;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const PredictionAPI = {
  getMatchPrediction: async (matchId: number): Promise<MatchPrediction> => {
    const response = await api.get(`/api/predictions/match/${matchId}`);
    return response.data;
  },

  getUpcomingPredictions: async (leagueId?: number, limit: number = 10): Promise<any> => {
    const url = leagueId 
      ? `/api/predictions/upcoming?league_id=${leagueId}&limit=${limit}`
      : `/api/predictions/upcoming?limit=${limit}`;
    const response = await api.get(url);
    return response.data;
  },

  getLeaguePredictions: async (leagueId: number): Promise<any> => {
    const response = await api.get(`/api/predictions/league/${leagueId}`);
    return response.data;
  },

  getMatchAnalysis: async (matchId: number): Promise<MatchAnalysis> => {
    const response = await api.get(`/api/predictions/analysis/${matchId}`);
    return response.data;
  },

  getMatches: async (): Promise<any> => {
    const response = await api.get('/test/matches');
    return response.data;
  },

// Add to PredictionAPI object:

// Get news
getNews: async (limit: number = 20): Promise<any> => {
  const response = await api.get(`/api/predictions/news?limit=${limit}`);
  return response.data;
},

// Get daily accuracy
getDailyAccuracy: async (date: string): Promise<any> => {
  const response = await api.get(`/api/predictions/accuracy/daily/${date}`);
  return response.data;
},

// Get league accuracy
getLeagueAccuracy: async (leagueId: number): Promise<any> => {
  const response = await api.get(`/api/predictions/accuracy/league/${leagueId}`);
  return response.data;
},

// Get match accuracy
getMatchAccuracy: async (matchId: number): Promise<any> => {
  const response = await api.get(`/api/predictions/accuracy/match/${matchId}`);
  return response.data;
},


// Get all leagues
getLeagues: async (): Promise<any> => {
  const response = await api.get('/api/predictions/leagues');
  return response.data;
},

// Get fixtures for a league
getFixtures: async (leagueId: number): Promise<any> => {
  const response = await api.get(`/api/predictions/fixtures/${leagueId}`);
  return response.data;
}
};