import { Summary } from "@/lib/types";

interface HeroProps {
  summary: Summary | null;
}

function Hero({ summary }: HeroProps) {
  const delayedGames = summary?.countDelayed ?? 0;
  const averageDelay = summary?.avgDelay ?? 0;

  return (
    <section className="hero">
      <div className="hero__eyebrow">NBA tip-off delay tracker</div>
      <h1>See which games actually started on time.</h1>
      <p className="hero__copy">
        Delayed compares scheduled tip to observed tip-off so you can see where
        the league is running late, then total up how much waiting time you have
        burned this season.
      </p>
      <div className="hero__stats">
        <div>
          <span>Delayed games in view</span>
          <strong>{delayedGames}</strong>
        </div>
        <div>
          <span>Average late start</span>
          <strong>{averageDelay.toFixed(1)} min</strong>
        </div>
      </div>
    </section>
  );
}

export default Hero;
