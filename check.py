import google.generativeai as genai

# ضع مفتاحك هنا
genai.configure(api_key="AIzaSyB4NMbPldqHfiRnwGPGx1RScMdMbDRE6ac")

print("جاري البحث عن الموديلات المتاحة لحسابك...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"حدث خطأ في الاتصال: {e}")