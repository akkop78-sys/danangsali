(() => {
  const header = document.querySelector(".site-header");
  const reveals = document.querySelectorAll(".reveal");

  const onScroll = () => {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 12);
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // 콘텐츠가 안 보이는 문제를 막기 위해 기본 표시
  reveals.forEach((el) => el.classList.add("is-visible"));

  if (!("IntersectionObserver" in window)) {
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.05, rootMargin: "0px 0px 0px 0px" }
  );

  reveals.forEach((el) => io.observe(el));
})();
