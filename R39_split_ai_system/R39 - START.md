**START: Input Section**  
**Resources**

* n8n: [https://n8n.partnerlinks.io/o3jqtj032c02](https://n8n.partnerlinks.io/o3jqtj032c02)  
* Telegram BotFather: [https://telegram.me/BotFather](https://telegram.me/BotFather)  
* OpenAI API key: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)  
* OpenAI where to add credits: [https://platform.openai.com/settings/organization/billing/overview](https://platform.openai.com/settings/organization/billing/overview)  
* Gsheet template: [**link**](https://docs.google.com/spreadsheets/d/1h6KgId2iWX3kzDYbIPnjVSsQ4W_Uilm0WunN4MKBVvk/copy)  
* Ideator GPT: [**link**](https://chatgpt.com/g/g-68b4f4fb3d908191a6e9510fc1cdb8ba-ideator-gpt-for-split-ai-system-by-robonuggets)

**📌 Important:** when sending a photo via Telegram, mark the "Compress the image" toggle as checked. This just lets n8n map to your image file correctly for this workflow

**Get Img Path**

https://api.telegram.org/bot{{ $('Set Bot ID').item.json\['bot id'\] }}/getFile?file\_id={{ $('Telegram Trigger').first(0,0).json.message.photo\[2\].file\_id }}

**Describe Img**

Analyze the given image and determine if it primarily depicts a product or a character, or BOTH.

\- If the image is of a product, return the analysis in YAML format with the following fields:

brand\_name: (Name of the brand shown in the image, if visible or inferable)

color\_scheme:

\- hex: (Hex code of each prominent color used)

name: (Descriptive name of the color)

font\_style: (Describe the font family or style used: serif/sans-serif, bold/thin, etc.)

visual\_description: (A full sentence or two summarizing what is seen in the image, ignoring the background)

\- If the image is of a character, return the analysis in YAML format with the following fields:

character\_name: (Name of the character if visible or inferable)

color\_scheme:

\- hex: (Hex code of each prominent color used on the character)

name: (Descriptive name of the color)

outfit\_style: (Description of clothing style, accessories, or notable features)

visual\_description: (A full sentence or two summarizing what the character looks like, ignoring the background)

Only return the YAML. Do not explain or add any other comments.

\- if it is BOTH, return both descriptions as guided above in YAML format

Image URL: https://api.telegram.org/file/bot{{ $('Set Bot ID').item.json\['bot id'\] }}/{{ $json.result.file\_path }}

IMPORTANT LINKS:  
[https://chatgpt.com/g/g-68b4f4fb3d908191a6e9510fc1cdb8ba-ideator-gpt-for-split-ai-system-by-robonuggets](https://chatgpt.com/g/g-68b4f4fb3d908191a6e9510fc1cdb8ba-ideator-gpt-for-split-ai-system-by-robonuggets) \- CHAT GPT IDEATOR  
