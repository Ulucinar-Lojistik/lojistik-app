import streamlit as st
import pandas as pd

st.set_page_config(page_title="Lojistik Sevkiyat Paneli", layout="wide")

if 'sevkiyatlar' not in st.session_state:
    st.session_state.sevkiyatlar = pd.DataFrame([
        {"SİPARİŞ NO": "NZL4369", "MÜŞTERİ": "A101", "DEPO": "İZMİR", "ÜRÜNLER": "1.50 LT PET SU", "PLAKA": "15AB175", "DURUM": "YÜKLENDİ"},
        {"SİPARİŞ NO": "NZL4367", "MÜŞTERİ": "BİM", "DEPO": "KONYA", "ÜRÜNLER": "0.50 LT PET SU", "PLAKA": "", "DURUM": "BEKLİYOR (BOŞTA)"},
    ])
if 'sofor_listesi' not in st.session_state:
    st.session_state.sofor_listesi = ["İbrahim Erdem (15AB175)", "Hasan Akın (15AL283)"]
if 'depo_listesi' not in st.session_state:
    st.session_state.depo_listesi = ["A101 - İZMİR", "BİM - KONYA", "ABANT SU - BURDUR"]

def satir_boya(row):
    if str(row["PLAKA"]).strip() == "":
        return ['background-color: #fef7e0; color: #b06000; font-weight: bold;'] * len(row)
    else:
        return ['background-color: #e6f4ea; color: #137333; font-weight: 600;'] * len(row)

st.sidebar.markdown("### 🚪 SİSTEM GİRİŞİ")
giris_turu = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"])

if giris_turu == "🚚 Şoför Ekranı (Sadece İzleme)":
    st.markdown("<h2 style='text-align: center; color: #1e3d59;'>🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU</h2>", unsafe_index=True)
    st.markdown("<h5 style='text-align: center; color: #17b978;'>• CANLI ŞOFÖR BİLGİLENDİRME PANOSU •</h5>", unsafe_index=True)
    st.divider()
    
    styled_df = st.session_state.sevkiyatlar.style.apply(satir_boya, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-top: 30px;'>🔄 Liste her dakika otomatik yenilenir. Boştaki (Turuncu) işler için sevkiyat amirliği ile görüşün.</p>", unsafe_index=True)

else:
    st.title("⚙️ Lojistik Yönetici Kontrol Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    
    if sifre == "1234":
        st.success("Giriş Başarılı. Veri ekleme ve güncelleme yapabilirsiniz.")
        st.subheader("📦 1. Hızlı Tanımlamalar (Hafızaya Alınacak Sabitler)")
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            with st.expander("👤 Yeni Şoför & Plaka Kaydet"):
                s_ad = st.text_input("Şoför Adı Soyadı:")
                s_plaka = st.text_input("Araç Plakası:")
                if st.button("💾 Şoförü Hafızaya Ekle"):
                    if s_ad and s_plaka:
                        st.session_state.sofor_listesi.append(f"{s_ad} ({s_plaka})")
                        st.success(f"{s_ad} hafızaya kaydedildi!")
                        
        with col_s2:
            with st.expander("🏢 Yeni Müşteri & Depo Kaydet"):
                m_ad = st.text_input("Müşteri / Firma Adı:")
                d_yer = st.text_input("Gideceği Yer/Şehir:")
                if st.button("💾 Depoyu Hafızaya Ekle"):
                    if m_ad and d_yer:
                        st.session_state.depo_listesi.append(f"{m_ad} - {d_yer}")
                        st.success(f"{m_ad} - {d_yer} hafızaya kaydedildi!")
        
        st.divider()
        st.subheader("➕ 2. Günlük Yeni İş Emri Ekle")
        with st.form("is_formu", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1: siparis_no = st.text_input("Sipariş Numarası:")
            with c2: secilen_yer = st.selectbox("Müşteri & Depo Seç (Hafızadan):", st.session_state.depo_listesi)
            with c3: urun_detay = st.text_input("Ürün Detayı:")
            
            if st.form_submit_button("🚀 Veriyi Havuza Gönder (Turuncu Yap)"):
                m_parca, d_parca = secilen_yer.split(" - ")
                yeni_is = {"SİPARİŞ NO": siparis_no, "MÜŞTERİ": m_parca, "DEPO": d_parca, "ÜRÜNLER": urun_detay, "PLAKA": "", "DURUM": "BEKLİYOR (BOŞTA)"}
                st.session_state.sevkiyatlar = pd.concat([st.session_state.sevkiyatlar, pd.DataFrame([yeni_is])], ignore_index=True)
                st.success("İş başarıyla eklendi!")
                st.rerun()

        st.divider()
        st.subheader("✍️ 3. Boştaki İşe Plaka / Şoför Ata")
        bostaki_isler = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["PLAKA"] == ""]["SİPARİŞ NO"].tolist()
        
        if bostaki_isler:
            cc1, cc2 = st.columns(2)
            with cc1: secilen_is = st.selectbox("Plaka Atanacak Sipariş No:", bostaki_isler)
            with cc2: secilen_sofor = st.selectbox("Atanacak Şoför & Araç (Hafızadan):", st.session_state.sofor_listesi)
            
            if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)"):
                plaka_ayikla = secilen_sofor.split("(")[1].replace(")", "")
                st.session_state.sevkiyatlar.loc[st.session_state.sevkiyatlar["SİPARİŞ NO"] == secilen_is, "PLAKA"] = plaka_ayikla
                st.session_state.sevkiyatlar.loc[st.session_state.sevkiyatlar["SİPARİŞ NO"] == secilen_is, "DURUM"] = "YÜKLENDİ"
                st.success("Plaka başarıyla atandı!")
                st.rerun()
        else:
            st.info("Havuzda plaka atanmayı bekleyen boşta iş yok.")
            
    elif sifre != "":
        st.error("Hatalı Yönetici Şifresi!")
