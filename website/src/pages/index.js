import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import styles from './index.module.css';

const features = [
  {
    stat: '0 bytes',
    label: 'Leave your machine',
    text: 'Text and audio are generated and kept on your PC. The server binds to localhost.',
  },
  {
    stat: '1 file',
    label: 'To add an engine',
    text: 'Drop an adapter into server/engines/. The UI reads the engine list from the server.',
  },
  {
    stat: 'No cap',
    label: 'On script length',
    text: 'Long text is split into sentence sized parts, played as they finish, then stitched into one WAV.',
  },
];

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout title="Local text to speech" description={siteConfig.tagline}>
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.copy}>
            <div className={styles.eyebrow}>
              <span className={styles.lamp} />
              Local, open, MIT
            </div>
            <h1 className={styles.title}>Speech that stays on your machine.</h1>
            <p className={styles.tagline}>
              Voice Room is a local text to speech studio with a console UI, long text
              playback and pluggable engines. No account, no upload, no per character bill.
            </p>
            <div className={styles.actions}>
              <Link className={styles.primary} to="/docs/quickstart">
                Start with the quickstart
              </Link>
              <Link
                className={styles.secondary}
                href="https://github.com/Raghav2012Code/voice-room/releases/tag/v0.1.0"
              >
                Download for Windows
              </Link>
              <Link className={styles.textLink} href="https://github.com/Raghav2012Code/voice-room">
                View source
              </Link>
            </div>
            <p className={styles.meta}>Python 3.10+ · Windows native app · Browser UI anywhere</p>
          </div>
          <div className={styles.shotWrap}>
            <img
              className={styles.shot}
              src={useBaseUrl('/img/voice-room.png')}
              alt="Voice Room console with engine rail, script box and monitor"
            />
          </div>
        </section>

        <section className={styles.features} aria-label="Highlights">
          {features.map((feature) => (
            <div className={styles.feature} key={feature.label}>
              <div className={styles.stat}>{feature.stat}</div>
              <div className={styles.label}>{feature.label}</div>
              <p className={styles.text}>{feature.text}</p>
            </div>
          ))}
        </section>

        <section className={styles.next}>
          <div>
            <h2 className={styles.nextTitle}>Read the docs, or read the code.</h2>
            <p className={styles.nextText}>
              The quickstart gets a sine wave engine talking in under a minute. The engine
              guide shows how to wire Phonon, Kokoro, Kitten, Chatterbox, or your own model.
            </p>
          </div>
          <div className={styles.nextLinks}>
            <Link className={styles.secondary} to="/docs/quickstart">
              Quickstart
            </Link>
            <Link className={styles.secondary} to="/docs/engines/adding-an-engine">
              Add an engine
            </Link>
            <Link className={styles.textLink} href="https://github.com/Raghav2012Code/voice-room">
              GitHub
            </Link>
          </div>
        </section>
      </main>
    </Layout>
  );
}
