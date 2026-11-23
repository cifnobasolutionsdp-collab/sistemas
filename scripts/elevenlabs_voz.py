"""Genera la locución de un reel con ElevenLabs y guarda los tiempos de cada palabra.

Uso:
    python scripts/elevenlabs_voz.py guion.json salida_dir [--voice-id ID] [--model eleven_v4]

guion.json es una lista de textos, uno por pantalla del reel. Por cada pantalla se
genera un MP3 (escena_N.mp3) y un JSON con las palabras y su tiempo de inicio y fin
(escena_N.json). La clave se lee de ELEVENLABS_API_KEY; nunca va en el código.
"""
import argparse
import base64
import json
import os

from elevenlabs import ElevenLabs

VOZ_YO_1 = "O5Qw8Chpbe9KesLQlNFf"


def palabras_desde_alineacion(al):
    """Agrupa la alineación por caracteres en palabras con inicio y fin en segundos."""
    chars, ini, fin = al.characters, al.character_start_times_seconds, al.character_end_times_seconds
    out, cur, t0, t1 = [], "", None, None
    for c, a, b in zip(chars, ini, fin):
        if c.isspace():
            if cur:
                out.append({"t": cur, "s": t0, "e": t1})
            cur, t0 = "", None
            continue
        if t0 is None:
            t0 = a
        cur += c
        t1 = b
    if cur:
        out.append({"t": cur, "s": t0, "e": t1})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("guion")
    ap.add_argument("salida")
    ap.add_argument("--voice-id", default=VOZ_YO_1)
    ap.add_argument("--model", default="eleven_v4")
    ap.add_argument("--stability", type=float, default=0.5)
    ap.add_argument("--similarity", type=float, default=0.8)
    args = ap.parse_args()

    textos = json.load(open(args.guion, encoding="utf-8"))
    os.makedirs(args.salida, exist_ok=True)
    client = ElevenLabs()  # lee ELEVENLABS_API_KEY del entorno
    total = 0
    for i, texto in enumerate(textos):
        if not texto.strip():
            continue
        r = client.text_to_speech.convert_with_timestamps(
            voice_id=args.voice_id,
            text=texto,
            model_id=args.model,
            language_code="es",
            previous_text=textos[i - 1] if i > 0 else None,
            next_text=textos[i + 1] if i + 1 < len(textos) else None,
            voice_settings={"stability": args.stability, "similarity_boost": args.similarity},
        )
        with open(os.path.join(args.salida, f"escena_{i}.mp3"), "wb") as f:
            f.write(base64.b64decode(r.audio_base_64))
        al = r.normalized_alignment or r.alignment
        with open(os.path.join(args.salida, f"escena_{i}.json"), "w", encoding="utf-8") as f:
            json.dump({"texto": texto, "palabras": palabras_desde_alineacion(al)}, f, ensure_ascii=False)
        total += len(texto)
        print(f"escena {i}: {len(texto)} caracteres")
    print(f"total: {total} caracteres")


if __name__ == "__main__":
    main()
