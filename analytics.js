(() => {
  const measurementId = "G-WN99333WLX";

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function gtag() {
    window.dataLayer.push(arguments);
  };

  window.gtag("js", new Date());
  window.gtag("config", measurementId, { cookie_domain: "auto" });

  const eventForLink = (link) => {
    const rawHref = link.getAttribute("href") || "";
    if (rawHref.startsWith("tel:")) return "phone_click";
    if (rawHref.startsWith("mailto:")) return "email_click";

    let url;
    try {
      url = new URL(link.href, window.location.href);
    } catch {
      return null;
    }

    if (url.hostname === "apply.jinhakapply.com") return "apply_click";
    if (url.hostname === "open.kakao.com") return "kakao_consult_click";
    if (url.hostname === "portfolio.k-bigdata.kr") return "portfolio_click";
    if (url.hostname === "www.youtube.com" || url.hostname === "youtube.com" || url.hostname === "youtu.be") return "youtube_click";
    return null;
  };

  document.addEventListener("click", (event) => {
    const link = event.target.closest("a");
    if (!link) return;

    const eventName = eventForLink(link);
    if (!eventName) return;

    const clickArea = link.closest("header")
      ? "header"
      : link.closest("footer")
        ? "footer"
        : link.closest(".mobile-apply")
          ? "mobile_cta"
          : "content";

    window.gtag("event", eventName, { click_area: clickArea });
  });
})();
