plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "dz.oummalak.manager"
    compileSdk = 35
    defaultConfig {
        applicationId = "dz.oummalak.manager"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
        buildConfigField("String", "SUPABASE_URL", "\"https://rlgbbkyrpkrfavpvivvg.supabase.co\"")
        val pubKey = providers.environmentVariable("SUPABASE_PUBLISHABLE_KEY").orNull ?: ""
        buildConfigField("String", "SUPABASE_KEY", "\""+pubKey+"\"")
    }
    buildFeatures { buildConfig = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    packaging { resources { excludes += "/META-INF/{AL2.0,LGPL2.1}" } }
}
