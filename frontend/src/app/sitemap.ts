import { MetadataRoute } from 'next';

const BASE_URL = 'https://www.hampsteadrenovations.co.uk/planning';

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: BASE_URL,
      lastModified: new Date('2026-03-06'),
      changeFrequency: 'monthly',
      priority: 1,
    },
    {
      url: `${BASE_URL}/coverage`,
      lastModified: new Date('2026-03-06'),
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/features`,
      lastModified: new Date('2026-03-06'),
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/how-it-works`,
      lastModified: new Date('2026-03-06'),
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/contact`,
      lastModified: new Date('2026-03-06'),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
  ];
}
