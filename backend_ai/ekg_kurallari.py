def tani_ve_aciklama_getir(kalp_hizi, qrs_genisligi, p_dalgasi_var_mi, yas_grubu="cocuk"):
    """
    Girilen EKG özelliklerine göre tanı ve tıp öğrencisi için açıklama döndürür.
    """
    
    # Supraventriküler Taşikardi (SVT) Kontrolü[cite: 1]
    if (yas_grubu == "cocuk" and kalp_hizi >= 180) or (yas_grubu == "bebek" and kalp_hizi >= 220):
        if qrs_genisligi <= 0.09 and not p_dalgasi_var_mi:
            tani = "Supraventriküler Taşikardi (SVT)"
            aciklama = "Öğrenci Notu: Kalp hızının yaşa göre kritik sınırın üzerinde olması (çocuklarda ≥180/dk, bebeklerde ≥220/dk), QRS kompleksinin dar (≤0.09 sn) olması ve P dalgasının yokluğu/anormalliği SVT ile uyumludur[cite: 1]."
            return tani, aciklama

    # Ventriküler Taşikardi (VT) Kontrolü[cite: 1]
    if kalp_hizi > 120 and qrs_genisligi > 0.09:
        tani = "Ventriküler Taşikardi (VT)"
        aciklama = "Öğrenci Notu: Geniş QRS (>0.09 sn) ve >120/dk kalp hızı saptandı[cite: 1]. Klinik kural: Net ayrımın yapılamadığı bütün geniş QRS'li taşikardiler aksi ispat edilinceye kadar VT gibi tedavi edilmelidir[cite: 1]."
        return tani, aciklama

    # Normal veya Diğer Durumlar
    return "Belirsiz / İleri İnceleme Gerekli", "Girilen parametreler temel taşikardi sınırlarıyla tam eşleşmiyor. P-QRS ilişkisini ve ST segmentini tekrar gözden geçirin."