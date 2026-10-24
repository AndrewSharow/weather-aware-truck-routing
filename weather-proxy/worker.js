const UPSTREAM = "https://api.open-meteo.com";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (request.method !== "GET" || url.pathname !== "/v1/forecast") {
      return new Response("Not found", { status: 404 });
    }
    return fetch(UPSTREAM + url.pathname + url.search);
  },
};
