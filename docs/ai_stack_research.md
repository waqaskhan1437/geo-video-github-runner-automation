# AI Video Stack Research (Forums + GitHub)

## Goal
Runner-based workflow for cinematic geo-conflict videos with:
- realistic map action layers,
- energetic/refined voiceover,
- iterative analysis -> refine -> retest loop,
- optional advanced GPU AI generation stack.

## Primary GitHub Repos
- ComfyUI (node-based generation engine): https://github.com/comfyanonymous/ComfyUI
- ComfyUI Manager (node/install management): https://github.com/ltdrdata/ComfyUI-Manager
- ComfyUI Video Helper Suite (video workflows): https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
- Diffusers (model pipelines/tooling): https://github.com/huggingface/diffusers
- CogVideo / CogVideoX (open video generation family): https://github.com/THUDM/CogVideo and https://github.com/THUDM/CogVideoX
- Edge TTS (high-quality neural TTS wrapper): https://github.com/rany2/edge-tts
- Piper TTS (offline open-source TTS): https://github.com/rhasspy/piper (archived) and successor fork https://github.com/danielswiss/piper
- Chatterbox TTS (expressive open-source speech): https://github.com/resemble-ai/chatterbox
- Kdenlive (open-source video editor): https://github.com/KDE/kdenlive
- Shotcut (open-source video editor): https://github.com/mltframework/shotcut

## Forum Signals (Community Usage Patterns)
- ComfyUI workflow/tool recommendations thread:
  https://www.reddit.com/r/comfyui/comments/1l61es6/looking_for_underrated_comfyui_workflows_tools/
- Image-to-video reliability discussion:
  https://www.reddit.com/r/StableDiffusion/comments/1f2rjrr/anybody_know_of_any_reliable_image_to_video/
- Practical ComfyUI user setup discussions:
  https://www.reddit.com/r/comfyui/comments/1f2axjx/i_want_to_make_a_image_to_video_reddit_stories/

## Runner Constraints and Execution Model
- GitHub-hosted runners are ephemeral and primarily CPU in default usage:
  https://docs.github.com/actions/concepts/runners
- GPU workflows are best handled by self-hosted runners:
  https://docs.github.com/actions/hosting-your-own-runners

## Practical Recommendation
- Use the default CPU workflow (`conflict-doc-ai-pipeline.yml`) for deterministic map/video+voice output with AI heuristic refinement.
- Use the optional self-hosted GPU workflow (`gpu-ai-stack-self-hosted.yml`) to auto-install ComfyUI stack and attach heavy text/image/video generation models when GPU is available.

