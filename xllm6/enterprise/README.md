The doc for <code>xllm-enterprise-v2.py</code> is in xllm-enterprise-v2.pdf. The previous version (xllm-enterprise.py) is no longer maintained. I also created a library <code>xllm_enterprise_util.py</code>. Both <code>xllm-enterprise-v2-user.py</code> and <code>xllm-enterprise-dev.py</code> use that library. The former is essentially the same as xllm-enterprise-v2.py but much shorter since all the functions have been moved to the library. The latter also uses the same algorithms and architecture with recent additions (relevancy scores) but it serves a different purpose: testing a large number of prompts.

<b>Notes</b>:

<ul>
<li>
  <code>xllm-enterprise-v2-user.py</code> calls the real-time fine-tuning function. The user enters one prompt at a time, from the keyboard, including command options.
</li>
  <li>
    <code>xllm-enterprise-v2-dev.py</code> does not call the real-time fine-tuning function. The test prompts with correct answers are loaded from a text file: <a href="https://github.com/VincentGranville/Large-Language-Models/blob/main/xllm6/enterprise/enterprise_sample_prompts.txt">enterprise_sample_prompts.txt</a>a>. A prompt and corresponding answer are in a same row, separated by " | ".
  </li>
</ul>
