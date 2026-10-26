# Native frame-generation HUD reference

Patch 0095 captures the pass-owned pre-HUD Native scene per presentation Frame and converts it through matching host postprocessing/output format. The matching output-sized image is supplied as HUDLessColor for interpolation UI extraction. Legacy images that may already contain HUD are not labeled HUD-less. Existing queue ordering and per-Frame fence ownership are retained; asynchronous generation remains disabled.

The user reported that driving HUD duplication appeared resolved. This is a rendering correction candidate with live positive feedback, not proof of correct frame spacing or a performance improvement. Full-resolution copy/conversion has a measurable cost; FG performance remains under investigation.

Validation: build, 2,893 imports, image self-test, real HUD-less input logs and live driving check.
