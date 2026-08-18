'use client';

import { useState, useEffect } from 'react';
import { PredictionAPI } from '@/app/services/api';

interface NewsItem {
  id: number;
  title: string;
  summary: string;
  source: string;
  url: string;
  image_url: string;
  published_at: string;
}

interface NewsFeedProps {
  leagueFilter?: string;
}

export default function NewsFeed({ leagueFilter }: NewsFeedProps = {}) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filteredNews, setFilteredNews] = useState<NewsItem[]>([]);

  useEffect(() => {
    fetchNews();
  }, []);

  useEffect(() => {
    if (leagueFilter) {
      setFilteredNews(
        news.filter((item) =>
          item.title?.toLowerCase().includes(leagueFilter.toLowerCase()) ||
          item.summary?.toLowerCase().includes(leagueFilter.toLowerCase())
        )
      );
    } else {
      setFilteredNews(news);
    }
  }, [news, leagueFilter]);

  const fetchNews = async () => {
    try {
      const data = await PredictionAPI.getNews(20);
      setNews(data);
      setFilteredNews(data);
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-gray-400">Loading news...</div>;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-700 p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-white">📰 Football News</h2>
        {leagueFilter && (
          <span className="text-xs text-blue-400 bg-blue-900/30 px-2 py-1 rounded">
            Filtered: {leagueFilter}
          </span>
        )}
        <button
          onClick={fetchNews}
          className="text-sm bg-gray-800 hover:bg-gray-700 px-3 py-1 rounded transition-colors"
        >
          🔄 Refresh
        </button>
      </div>
      <div className="space-y-4">
        {filteredNews.length === 0 ? (
          <p className="text-gray-400">No news available{leagueFilter ? ` for ${leagueFilter}` : ''}</p>
        ) : (
          filteredNews.map((item) => (
            <div key={item.id} className="border-b border-gray-700 pb-4 last:border-0">
              <a href={item.url} target="_blank" rel="noopener noreferrer">
                <h3 className="text-white font-medium hover:text-blue-400 transition-colors">
                  {item.title}
                </h3>
              </a>
              <p className="text-gray-400 text-sm mt-1">{item.summary}</p>
              <div className="flex justify-between items-center mt-2">
                <span className="text-gray-500 text-xs">{item.source}</span>
                <span className="text-gray-500 text-xs">
                  {new Date(item.published_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}