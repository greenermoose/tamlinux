# Owned speaker tuning payload

The command package installs this MIT-licensed payload at
`share/tamlinux/audio`; `tam-audio-tuning` reads it relative to its installed
executable. `TAMLINUX_AUDIO_DATA` can explicitly select a trusted custom payload.

The dedicated native PipeWire client uses `tamlinux-speaker-tuning.conf` and
`tamlinux-speaker-tuning.service`. The graph exports `tamlinux_speaker_tuning`
and its output stream. Tuning is optional and checks hardware, the live sink,
EasyEffects and the native LV2 limiter before writing/starting a client.

See [audio closure and recovery](../../docs/plans/0.4.3-audio-output-closure.md)
for mutable state, preserved originals, provider boundaries and remaining
migration/physical proof. The profile's historical measurements are retained
provenance; this transfer did not remeasure any speakers.
