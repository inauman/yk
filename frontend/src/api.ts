export async function storeSeed() {
  const res = await fetch('/api/v1/seed/store', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  return res.json();
}

export async function retrieveSeed() {
  const res = await fetch('/api/v1/seed/retrieve');
  return res.json();
} 