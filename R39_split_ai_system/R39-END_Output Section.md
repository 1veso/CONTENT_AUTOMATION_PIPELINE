**END: Output Section**  
**Resources**

* File storage recommended: [Box.com](http://box.com/)  
* Openrouter sign up: [https://openrouter.ai/](https://openrouter.ai/)

**📌 NOTE:** OpenRouter has unfortunately hidden their free version of nanobanana as of Sept 6 2025 😔 You can still use their version at 4 cents per image (which is still cheap\!) if you change the model in the body below to "google/gemini-2.5-flash-image-preview" (basically just removing the word free). You can also check [**this tutorial**](https://www.skool.com/robonuggets/classroom/f7fbb41f?md=4e545f9f9fc146d483b193e961ac3adf&utm_campaign=skool_link_classroom&utm_content=72de1ab0f0734bfab9d4d266adf08025) on an improved version of this workflow for 2 cents per image via Kie AI

**HTTP Request \- nanobanana**

url: https://openrouter.ai/api/v1/chat/completions

body

```
{
  "model": "google/gemini-2.5-flash-image-preview:free",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "{{ $json.output.image_prompt.replace(/\"/g, '\\\"').replace(/\n/g, '\\n') }}"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "https://api.telegram.org/file/bot{{ $('Set Bot ID').first().json['bot id'] }}/{{ $('Get Img Path').first().json.result.file_path }}"
          }
        }
      ]
    }
  ]
}
```

**Set Base**

{{$json\["choices"\]\[0\]\["message"\]\["images"\]\[0\]\["image\_url"\]\["url"\].split(",")\[1\]}}

**Box file name**

{{ $('Get Rows to Create').item.json.index }}\_{{ $('Get Rows to Create').item.json.ad\_copy }}\_{{ $('Nanobanana').item.json.id }}.png

**Gsheet**

Success file\_name \= {{ $json.name }}

Error file\_name \= {{ $('Nanobanana').item.json.choices\[0\].native\_finish\_reason }}

PLUS REFER TO: **R39 \- FYI Box Set up** 