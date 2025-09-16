export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).end();
  }
  // Optionally verify signature: req.headers['x-ebay-signature']
  return res.status(204).end(); // Immediately acknowledge
}
