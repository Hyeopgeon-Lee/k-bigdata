const slug = new URLSearchParams(location.search).get('slug');

if (slug && /^[a-z0-9-]+$/.test(slug)) {
  location.replace(`/insights/${encodeURIComponent(slug)}/`);
} else {
  location.replace('/#stories');
}
