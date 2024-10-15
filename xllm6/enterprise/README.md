The tech doc for <code>xllm-enterprise-v2.py</code> is <a href="https://github.com/VincentGranville/Large-Language-Models/blob/main/xllm6/enterprise/xllm-enterprise-v2.pdf">xllm-enterprise-v2.pdf</a>. The previous version (xllm-enterprise.py) is no longer maintained. I also created a library <code>xllm_enterprise_util.py</code>. Both <code>xllm-enterprise-v2-user.py</code> and <code>xllm-enterprise-dev.py</code> use that library. The former is essentially the same as xllm-enterprise-v2.py but much shorter since all the functions have been moved to the library. The latter also uses the same algorithms and architecture with recent additions (relevancy scores) but it serves a different purpose: testing a large number of prompts.

All input data (repository.txt augmented with repository2.txt) comes from one part of an anonymized corporate corpus, dealing with one sub-LLM. The augmented data (concatetation of the two files) is in repository3.txt.

<b>Notes</b>:

<ul>
<li>
  <code>xllm-enterprise-v2-user.py</code> calls the real-time fine-tuning function. The user enters one prompt at a time, from the keyboard, including command options.
</li>
  <li>
    <code>xllm-enterprise-v2-dev.py</code> does not call the real-time fine-tuning function. The test prompts with correct answers are loaded from a text file: <a href="https://github.com/VincentGranville/Large-Language-Models/blob/main/xllm6/enterprise/enterprise_sample_prompts.txt">enterprise_sample_prompts.txt</a>. A prompt and corresponding answer are in a same row, separated by " | ". For documentation, see <a href="https://github.com/VincentGranville/Large-Language-Models/blob/main/xllm6/enterprise/LLM-scores.pdf">LLM-scores.pdf</a>.
  </li>
</ul>

<b>More documentation</b>: 

All the material is documented in my book "Building Disruptive AI & LLM Apps from Scratch", abailable on MLtechniques.com e-store, <a href="https://mltechniques.com/shop/">here</a>. 

Additional resources:

<ul>
  <li>
See <a href="https://mltblog.com/47DisG5">here</a>.
  </li>
  <ul>
