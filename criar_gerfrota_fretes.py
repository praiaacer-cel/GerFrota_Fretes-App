#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
  GERADOR DO PROJETO GerFrota Fretes v2.1 - VERSÃO FINAL
=============================================================
  App Android para gestão de fretes com:
  • 9 Formas de Pagamento específicas (PIX PF, VITALI, COOP, etc.)
  • Relatórios de Adiantamento e Saldo por Forma de Pagamento
  • Sistema de Backup em 3 etapas (Local, Upload Drive, Download Drive)
  • Filtros por transportadora e placa
  • Entrada por voz e Exportação PDF
  
  USO: python3 criar_gerfrota_fretes.py
=============================================================
"""

import os
import sys

PROJETO = "GerFrotaFretesApp"
A = {}

# 1. settings.gradle.kts (COM REPOSITÓRIO MAVEN EXPLÍCITO PARA GARANTIR RESOLUÇÃO)
A["settings.gradle.kts"] = r'''pluginManagement {
    repositories { 
        google()
        mavenCentral()
        gradlePluginPortal() 
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://repo1.maven.org/maven2/") } // Fallback explícito para GitHub Actions
    }
}
rootProject.name = "GerFrotaFretes"
include(":app")
'''

# 2. build.gradle.kts (raiz)
A["build.gradle.kts"] = r'''plugins {
    id("com.android.application") version "8.2.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.20" apply false
    id("com.google.devtools.ksp") version "1.9.20-1.0.14" apply false
}
'''

# 3. gradle.properties
A["gradle.properties"] = r'''org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
'''

# 4. app/build.gradle.kts (COM VERSÃO ESTÁVEL DA API DO DRIVE)
A["app/build.gradle.kts"] = r'''plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp")
}
android {
    namespace = "com.gerfrota.fretes"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.gerfrota.fretes"
        minSdk = 26
        targetSdk = 34
        versionCode = 2
        versionName = "2.1"
    }
    buildFeatures { compose = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.4" }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildTypes { release { isMinifyEnabled = false } }
}
dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.7.7")
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")
    
    // Google Drive API - Versão estável e comprovada no Maven Central
    implementation("com.google.api-client:google-api-client-android:2.2.0") { 
        exclude(group = "org.apache.httpcomponents") 
    }
    implementation("com.google.apis:google-api-services-drive:v3-rev20220815-2.0.0") { 
        exclude(group = "org.apache.httpcomponents") 
    }
    implementation("com.google.auth:google-auth-library-oauth2-http:1.19.0")
    implementation("com.google.android.gms:play-services-auth:21.0.0")
}
'''

# 5. AndroidManifest.xml
A["app/src/main/AndroidManifest.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.RECORD_AUDIO"/>
    <uses-permission android:name="android.permission.GET_ACCOUNTS"/>
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28"/>
    <application android:allowBackup="true" android:icon="@mipmap/ic_launcher" android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round" android:supportsRtl="true" android:theme="@style/Theme.GerFrotaFretes">
        <activity android:name=".MainActivity" android:exported="true" android:theme="@style/Theme.GerFrotaFretes">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        <provider android:name="androidx.core.content.FileProvider" android:authorities="${applicationId}.fileprovider"
            android:exported="false" android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/file_paths"/>
        </provider>
    </application>
</manifest>
'''

# 6. PlacaEntity.kt
A["app/src/main/java/com/gerfrota/fretes/data/PlacaEntity.kt"] = r'''package com.gerfrota.fretes.data
import androidx.room.Entity
import androidx.room.PrimaryKey
@Entity(tableName = "placas")
data class PlacaEntity(@PrimaryKey val placa: String, val ativa: Boolean = true, val dataCadastro: Long = System.currentTimeMillis())
object PlacasPadrao { val lista = listOf("MLH 6C45", "QEW 8G04", "IWU 3D11", "ITL 4F00", "IXL 6H19") }
'''

# 7. FreteEntity.kt
A["app/src/main/java/com/gerfrota/fretes/data/FreteEntity.kt"] = r'''package com.gerfrota.fretes.data
import androidx.room.Entity
import androidx.room.PrimaryKey
@Entity(tableName = "fretes")
data class FreteEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0, val data: String, val placa: String, val valorFrete: Double,
    val adiantamento: Double, val formaPgtoAdiant: String, val saldoFrete: Double, val formaPgtoSaldo: String,
    val recebido: Boolean, val transportadora: String, val origem: String, val destino: String, val syncStatus: Int = 0
)
object FormasPagamento {
    val opcoes = listOf("PIX PF", "PIX VITALI", "PIX COOP", "PIX MOTORISTA",
        "DEP. CTA. PF", "DEP. CTA. VITALI", "DEP. CTA. COOP", "DEP. CTA MOTORISTA", "CHEQUE")
}
data class PlacaResumo(val placa: String, val totalFretes: Int, val totalValor: Double, val totalAdiantamento: Double, val totalSaldo: Double, val totalRecebido: Double)
data class ResumoFormaPagto(val formaPagto: String, val totalFretes: Int, val totalValor: Double)
'''

# 8. PlacaDao.kt
A["app/src/main/java/com/gerfrota/fretes/data/PlacaDao.kt"] = r'''package com.gerfrota.fretes.data
import androidx.room.*
import kotlinx.coroutines.flow.Flow
@Dao
interface PlacaDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun insert(placa: PlacaEntity)
    @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun insertAll(placas: List<PlacaEntity>)
    @Update suspend fun update(placa: PlacaEntity)
    @Delete suspend fun delete(placa: PlacaEntity)
    @Query("DELETE FROM placas WHERE placa = :placa") suspend fun deleteByPlaca(placa: String)
    @Query("SELECT * FROM placas WHERE ativa = 1 ORDER BY dataCadastro DESC") fun getAllAtivas(): Flow<List<PlacaEntity>>
    @Query("SELECT * FROM placas ORDER BY dataCadastro DESC") fun getAll(): Flow<List<PlacaEntity>>
    @Query("SELECT placa FROM placas WHERE ativa = 1 ORDER BY placa ASC") fun getAllPlacasAtivas(): Flow<List<String>>
    @Query("SELECT COUNT(*) FROM placas WHERE placa = :placa") suspend fun countByPlaca(placa: String): Int
    @Query("UPDATE placas SET ativa = 0 WHERE placa = :placa") suspend fun desativar(placa: String)
    @Query("UPDATE placas SET ativa = 1 WHERE placa = :placa") suspend fun ativar(placa: String)
}
'''

# 9. FreteDao.kt
A["app/src/main/java/com/gerfrota/fretes/data/FreteDao.kt"] = r'''package com.gerfrota.fretes.data
import androidx.room.*
import kotlinx.coroutines.flow.Flow
@Dao
interface FreteDao {
    @Insert suspend fun insert(frete: FreteEntity)
    @Insert suspend fun insertAll(fretes: List<FreteEntity>)
    @Update suspend fun update(frete: FreteEntity)
    @Delete suspend fun delete(frete: FreteEntity)
    @Query("DELETE FROM fretes") suspend fun deleteAll()
    @Query("SELECT COUNT(*) FROM fretes") suspend fun count(): Int
    @Query("SELECT * FROM fretes ORDER BY id DESC") fun getAll(): Flow<List<FreteEntity>>
    @Query("SELECT * FROM fretes WHERE id = :id") suspend fun getById(id: Long): FreteEntity?
    @Query("SELECT * FROM fretes WHERE recebido = 0 ORDER BY id DESC") fun getNaoRecebidos(): Flow<List<FreteEntity>>
    @Query("SELECT * FROM fretes WHERE transportadora = :transportadora ORDER BY id DESC") fun getPorTransportadora(transportadora: String): Flow<List<FreteEntity>>
    @Query("SELECT * FROM fretes WHERE placa = :placa ORDER BY id DESC") fun getPorPlaca(placa: String): Flow<List<FreteEntity>>
    @Query("SELECT transportadora, SUM(saldoFrete) as total FROM fretes WHERE recebido = 0 GROUP BY transportadora ORDER BY total DESC")
    fun saldoPorTransportadora(): Flow<List<SaldoTransportadora>>
    @Query("SELECT SUM(saldoFrete) FROM fretes WHERE recebido = 0") fun saldoTotalAReceber(): Flow<Double?>
    @Query("SELECT SUM(adiantamento) FROM fretes") fun totalAdiantamentos(): Flow<Double?>
    @Query("""
        SELECT placa, COUNT(*) as totalFretes, SUM(valorFrete) as totalValor, SUM(adiantamento) as totalAdiantamento,
               SUM(saldoFrete) as totalSaldo, SUM(CASE WHEN recebido = 1 THEN saldoFrete ELSE 0 END) as totalRecebido
        FROM fretes GROUP BY placa ORDER BY totalSaldo DESC
    """)
    fun resumoPorPlaca(): Flow<List<PlacaResumo>>
    @Query("SELECT * FROM fretes WHERE placa = :placa ORDER BY id DESC") fun getFretesPorPlaca(placa: String): Flow<List<FreteEntity>>
    @Query("SELECT DISTINCT transportadora FROM fretes ORDER BY transportadora") fun getAllTransportadoras(): Flow<List<String>>
    
    @Query("""
        SELECT formaPgtoAdiant as formaPagto, COUNT(*) as totalFretes, SUM(adiantamento) as totalValor
        FROM fretes WHERE adiantamento > 0 GROUP BY formaPgtoAdiant ORDER BY totalValor DESC
    """)
    fun resumoAdiantamentoPorForma(): Flow<List<ResumoFormaPagto>>
    
    @Query("""
        SELECT formaPgtoSaldo as formaPagto, COUNT(*) as totalFretes, SUM(saldoFrete) as totalValor
        FROM fretes WHERE saldoFrete > 0 AND recebido = 0 GROUP BY formaPgtoSaldo ORDER BY totalValor DESC
    """)
    fun resumoSaldoPorForma(): Flow<List<ResumoFormaPagto>>
    
    @Query("SELECT * FROM fretes WHERE formaPgtoAdiant = :forma ORDER BY id DESC") fun getFretesPorFormaAdiant(forma: String): Flow<List<FreteEntity>>
    @Query("SELECT * FROM fretes WHERE formaPgtoSaldo = :forma AND recebido = 0 ORDER BY id DESC") fun getFretesPorFormaSaldo(forma: String): Flow<List<FreteEntity>>
}
data class SaldoTransportadora(val transportadora: String, val total: Double)
'''

# 10. AppDatabase.kt
A["app/src/main/java/com/gerfrota/fretes/data/AppDatabase.kt"] = r'''package com.gerfrota.fretes.data
import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
@Database(entities = [FreteEntity::class, PlacaEntity::class], version = 2, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun freteDao(): FreteDao
    abstract fun placaDao(): PlacaDao
    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("""CREATE TABLE IF NOT EXISTS `placas` (`placa` TEXT NOT NULL PRIMARY KEY, `ativa` INTEGER NOT NULL DEFAULT 1, `dataCadastro` INTEGER NOT NULL DEFAULT 0)""")
                PlacasPadrao.lista.forEach { placa ->
                    db.execSQL("INSERT OR IGNORE INTO `placas` (placa, ativa, dataCadastro) VALUES ('$placa', 1, ${System.currentTimeMillis()})")
                }
            }
        }
        fun get(context: Context): AppDatabase = INSTANCE ?: synchronized(this) {
            INSTANCE ?: Room.databaseBuilder(context.applicationContext, AppDatabase::class.java, "gerfrota.db")
                .addMigrations(MIGRATION_1_2).build().also { INSTANCE = it }
        }
    }
}
'''

# 11. Repository.kt
A["app/src/main/java/com/gerfrota/fretes/data/Repository.kt"] = r'''package com.gerfrota.fretes.data
import kotlinx.coroutines.flow.Flow
class Repository(private val dao: FreteDao, private val placaDao: PlacaDao) {
    val fretes: Flow<List<FreteEntity>> = dao.getAll()
    val fretesNaoRecebidos: Flow<List<FreteEntity>> = dao.getNaoRecebidos()
    val saldoPorTransportadora: Flow<List<SaldoTransportadora>> = dao.saldoPorTransportadora()
    val saldoTotal: Flow<Double?> = dao.saldoTotalAReceber()
    val totalAdiantamentos: Flow<Double?> = dao.totalAdiantamentos()
    val resumoPorPlaca: Flow<List<PlacaResumo>> = dao.resumoPorPlaca()
    val resumoAdiantamentoPorForma: Flow<List<ResumoFormaPagto>> = dao.resumoAdiantamentoPorForma()
    val resumoSaldoPorForma: Flow<List<ResumoFormaPagto>> = dao.resumoSaldoPorForma()
    val placasAtivas: Flow<List<PlacaEntity>> = placaDao.getAllAtivas()
    val placasLista: Flow<List<String>> = placaDao.getAllPlacasAtivas()
    val todasPlacas: Flow<List<PlacaEntity>> = placaDao.getAll()
    val transportadoras: Flow<List<String>> = dao.getAllTransportadoras()
    suspend fun insert(f: FreteEntity) = dao.insert(f)
    suspend fun insertAll(fretes: List<FreteEntity>) = dao.insertAll(fretes)
    suspend fun update(f: FreteEntity) = dao.update(f)
    suspend fun delete(f: FreteEntity) = dao.delete(f)
    suspend fun deleteAll() = dao.deleteAll()
    suspend fun count(): Int = dao.count()
    suspend fun getById(id: Long): FreteEntity? = dao.getById(id)
    fun fretesPorPlaca(placa: String): Flow<List<FreteEntity>> = dao.getFretesPorPlaca(placa)
    fun fretesPorTransportadora(transportadora: String): Flow<List<FreteEntity>> = dao.getPorTransportadora(transportadora)
    fun fretesPorFormaAdiant(forma: String): Flow<List<FreteEntity>> = dao.getFretesPorFormaAdiant(forma)
    fun fretesPorFormaSaldo(forma: String): Flow<List<FreteEntity>> = dao.getFretesPorFormaSaldo(forma)
    suspend fun insertPlaca(placa: PlacaEntity) = placaDao.insert(placa)
    suspend fun insertPlacas(placas: List<PlacaEntity>) = placaDao.insertAll(placas)
    suspend fun updatePlaca(placa: PlacaEntity) = placaDao.update(placa)
    suspend fun deletePlaca(placa: PlacaEntity) = placaDao.delete(placa)
    suspend fun deletePlacaByNome(placa: String) = placaDao.deleteByPlaca(placa)
    suspend fun placaExiste(placa: String): Boolean = placaDao.countByPlaca(placa) > 0
    suspend fun desativarPlaca(placa: String) = placaDao.desativar(placa)
    suspend fun ativarPlaca(placa: String) = placaDao.ativar(placa)
}
'''

# 12. AuthManager.kt
A["app/src/main/java/com/gerfrota/fretes/data/AuthManager.kt"] = r'''package com.gerfrota.fretes.data
import android.content.Context
import android.content.SharedPreferences
import java.security.MessageDigest
object AuthManager {
    private const val PREFS = "gerfrota_auth"
    private fun prefs(ctx: Context): SharedPreferences = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    private fun hash(password: String): String {
        val md = MessageDigest.getInstance("SHA-256")
        return md.digest(password.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
    }
    fun registrar(ctx: Context, email: String, password: String): Boolean {
        if (email.isBlank() || password.length < 4) return false
        prefs(ctx).edit().apply { putString("email", email.trim().lowercase()); putString("pass_hash", hash(password)); putBoolean("logged", true); apply() }
        return true
    }
    fun login(ctx: Context, email: String, password: String): LoginResult {
        val p = prefs(ctx)
        val savedEmail = p.getString("email", null)
        val savedHash = p.getString("pass_hash", null)
        if (savedEmail == null || savedHash == null) return LoginResult.NOT_REGISTERED
        if (savedEmail != email.trim().lowercase()) return LoginResult.WRONG_EMAIL
        if (savedHash != hash(password)) return LoginResult.WRONG_PASSWORD
        p.edit().putBoolean("logged", true).apply()
        return LoginResult.SUCCESS
    }
    fun logout(ctx: Context) { prefs(ctx).edit().putBoolean("logged", false).apply() }
    fun isLogged(ctx: Context): Boolean = prefs(ctx).getBoolean("logged", false)
    fun getEmail(ctx: Context): String? = prefs(ctx).getString("email", null)
    fun isRegistered(ctx: Context): Boolean = prefs(ctx).contains("email")
}
enum class LoginResult { SUCCESS, WRONG_EMAIL, WRONG_PASSWORD, NOT_REGISTERED }
'''

# 13. LocalBackupManager.kt
A["app/src/main/java/com/gerfrota/fretes/data/LocalBackupManager.kt"] = r'''package com.gerfrota.fretes.data
import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

object LocalBackupManager {
    suspend fun criarBackupLocal(context: Context, fretes: List<FreteEntity>): Pair<Boolean, String> = withContext(Dispatchers.IO) {
        runCatching {
            val fileName = "gerfrota_backup_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale("pt", "BR")).format(Date())}.json"
            val backupDir = File(context.filesDir, "backups").apply { if (!exists()) mkdirs() }
            val backupFile = File(backupDir, fileName)
            val jsonArray = JSONArray()
            fretes.forEach { f ->
                jsonArray.put(JSONObject().apply {
                    put("id", f.id); put("data", f.data); put("placa", f.placa); put("valorFrete", f.valorFrete)
                    put("adiantamento", f.adiantamento); put("formaPgtoAdiant", f.formaPgtoAdiant); put("saldoFrete", f.saldoFrete)
                    put("formaPgtoSaldo", f.formaPgtoSaldo); put("recebido", f.recebido); put("transportadora", f.transportadora)
                    put("origem", f.origem); put("destino", f.destino); put("syncStatus", f.syncStatus)
                })
            }
            backupFile.writeText(jsonArray.toString(2))
            Pair(true, backupFile.absolutePath)
        }.getOrElse { Pair(false, "Erro: ${it.message}") }
    }
    
    suspend fun restaurarBackupLocal(context: Context, filePath: String): Pair<Boolean, List<FreteEntity>> = withContext(Dispatchers.IO) {
        runCatching {
            val file = File(filePath)
            if (!file.exists()) return@withContext Pair(false, emptyList())
            val jsonArray = JSONArray(file.readText())
            val fretes = mutableListOf<FreteEntity>()
            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                fretes.add(FreteEntity(id = obj.optLong("id", 0), data = obj.optString("data", ""), placa = obj.optString("placa", ""),
                    valorFrete = obj.optDouble("valorFrete", 0.0), adiantamento = obj.optDouble("adiantamento", 0.0),
                    formaPgtoAdiant = obj.optString("formaPgtoAdiant", ""), saldoFrete = obj.optDouble("saldoFrete", 0.0),
                    formaPgtoSaldo = obj.optString("formaPgtoSaldo", ""), recebido = obj.optBoolean("recebido", false),
                    transportadora = obj.optString("transportadora", ""), origem = obj.optString("origem", ""),
                    destino = obj.optString("destino", ""), syncStatus = obj.optInt("syncStatus", 0)))
            }
            // CORREÇÃO AQUI: .toList() garante que o retorno seja List<FreteEntity> e não MutableList
            Pair(true, fretes.toList()) 
        }.getOrElse { Pair(false, emptyList()) }
    }
}
'''

# 14. PdfExporter.kt
A["app/src/main/java/com/gerfrota/fretes/data/PdfExporter.kt"] = r'''package com.gerfrota.fretes.data
import android.content.Context
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.net.Uri
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*
object PdfExporter {
    data class PdfResult(val success: Boolean, val message: String, val uri: Uri? = null)
    suspend fun exportar(context: Context, fretes: List<FreteEntity>, titulo: String = "Relatorio de Fretes"): PdfResult = withContext(Dispatchers.IO) {
        runCatching {
            val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
            val df = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale("pt", "BR"))
            val pdf = PdfDocument()
            val pageW = 595; val pageH = 842; val margin = 30f
            val pTitle = Paint().apply { color = Color.parseColor("#0D47A1"); textSize = 20f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pSub = Paint().apply { color = Color.parseColor("#1976D2"); textSize = 11f; isAntiAlias = true }
            val pHead = Paint().apply { color = Color.WHITE; textSize = 9f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pCell = Paint().apply { color = Color.BLACK; textSize = 8f; isAntiAlias = true }
            val pBold = Paint().apply { color = Color.BLACK; textSize = 8f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pBgH = Paint().apply { color = Color.parseColor("#1976D2") }
            val pBgA = Paint().apply { color = Color.parseColor("#F5F5F5") }
            val pBord = Paint().apply { color = Color.parseColor("#BDBDBD"); style = Paint.Style.STROKE; strokeWidth = 0.5f }
            val pTot = Paint().apply { color = Color.parseColor("#0D47A1"); textSize = 12f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val colX = floatArrayOf(margin, margin + 50, margin + 100, margin + 180, margin + 290, margin + 340, margin + 390, margin + 440, margin + 485)
            val headers = arrayOf("Data", "Placa", "Transportadora", "Rota", "Valor", "Adiant.", "Saldo", "Status")
            val rowH = 16f; val headerY = 100f; val rowsPerPage = 40
            val totalPag = kotlin.math.max(1, kotlin.math.ceil(fretes.size.toDouble() / rowsPerPage).toInt())
            var tV = 0.0; var tA = 0.0; var tS = 0.0; var tRecebido = 0.0
            for (pg in 0 until totalPag) {
                val page = pdf.startPage(PdfDocument.PageInfo.Builder(pageW, pageH, pg).create())
                val c = page.canvas
                c.drawText(titulo, margin, 40f, pTitle)
                c.drawText("Gerado em ${df.format(Date())} - Pagina ${pg + 1} de $totalPag", margin, 58f, pSub)
                c.drawLine(margin, 70f, pageW - margin, 70f, pBord)
                c.drawRect(margin, headerY - 12f, pageW - margin, headerY + 4f, pBgH)
                headers.forEachIndexed { i, h -> c.drawText(h, colX[i], headerY, pHead) }
                val ini = pg * rowsPerPage
                val fim = kotlin.math.min(ini + rowsPerPage, fretes.size)
                var y = headerY + rowH
                for (idx in ini until fim) {
                    val f = fretes[idx]
                    if ((idx - ini) % 2 == 1) c.drawRect(margin, y - 10f, pageW - margin, y + 6f, pBgA)
                    c.drawText(f.data, colX[0], y, pCell)
                    c.drawText(f.placa, colX[1], y, pCell)
                    c.drawText(f.transportadora.ifBlank { "-" }, colX[2], y, pCell)
                    c.drawText("${f.origem.ifBlank{"-"}} -> ${f.destino.ifBlank{"-"}}".take(22), colX[3], y, pCell)
                    c.drawText(nf.format(f.valorFrete), colX[4], y, pCell)
                    c.drawText(nf.format(f.adiantamento), colX[5], y, pCell)
                    c.drawText(nf.format(f.saldoFrete), colX[6], y, if (f.saldoFrete > 0) pBold else pCell)
                    c.drawText(if (f.recebido) "Recebido" else "Pendente", colX[7], y, if (f.recebido) Paint().apply { color = Color.GREEN; textSize = 8f } else Paint().apply { color = Color.RED; textSize = 8f })
                    tV += f.valorFrete; tA += f.adiantamento; tS += f.saldoFrete
                    if (f.recebido) tRecebido += f.saldoFrete
                    y += rowH
                }
                c.drawRect(margin, headerY - 12f, pageW - margin, y, pBord)
                if (pg == totalPag - 1) {
                    val ty = y + 25f
                    c.drawText("RESUMO:", margin, ty, pTot)
                    c.drawText("Total Fretes: ${nf.format(tV)}", margin, ty + 18f, pBold)
                    c.drawText("Total Adiantamentos: ${nf.format(tA)}", margin + 150f, ty + 18f, pBold)
                    c.drawText("Total Recebido: ${nf.format(tRecebido)}", margin + 320f, ty + 18f, Paint().apply { color = Color.GREEN; textSize = 12f; isAntiAlias = true })
                    c.drawText("Saldo a Receber: ${nf.format(tS)}", margin + 320f, ty + 36f, Paint().apply { color = Color.RED; textSize = 12f; isAntiAlias = true })
                    c.drawText("Total de registros: ${fretes.size}", margin, ty + 56f, pSub)
                }
                pdf.finishPage(page)
            }
            val fileName = "GerFrota_Relatorio_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale("pt","BR")).format(Date())}.pdf"
            val folder = File(context.filesDir, "relatorios").apply { if (!exists()) mkdirs() }
            val file = File(folder, fileName)
            FileOutputStream(file).use { out -> pdf.writeTo(out) }
            pdf.close()
            PdfResult(true, "Relatorio gerado!", FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file))
        }.getOrElse { PdfResult(false, "Erro: ${it.message}") }
    }
    suspend fun exportarAdiantamentoPorForma(context: Context, resumo: List<ResumoFormaPagto>, fretes: List<FreteEntity>): PdfResult = withContext(Dispatchers.IO) {
        runCatching {
            val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
            val df = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale("pt", "BR"))
            val pdf = PdfDocument()
            val pageW = 595; val pageH = 842; val margin = 30f
            val pTitle = Paint().apply { color = Color.parseColor("#0D47A1"); textSize = 20f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pSub = Paint().apply { color = Color.parseColor("#1976D2"); textSize = 11f; isAntiAlias = true }
            val pHead = Paint().apply { color = Color.WHITE; textSize = 9f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pCell = Paint().apply { color = Color.BLACK; textSize = 8f; isAntiAlias = true }
            val pBold = Paint().apply { color = Color.BLACK; textSize = 8f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pBgH = Paint().apply { color = Color.parseColor("#4CAF50") }
            val pBgA = Paint().apply { color = Color.parseColor("#F5F5F5") }
            val pBord = Paint().apply { color = Color.parseColor("#BDBDBD"); style = Paint.Style.STROKE; strokeWidth = 0.5f }
            val pTot = Paint().apply { color = Color.parseColor("#0D47A1"); textSize = 12f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val colX = floatArrayOf(margin, margin + 60, margin + 120, margin + 200, margin + 280, margin + 360, margin + 440)
            val headers = arrayOf("Data", "Placa", "Transportadora", "Rota", "Forma Pgto", "Valor Adiant.")
            val rowH = 16f; val headerY = 100f; val rowsPerPage = 40
            val fretesAdiant = fretes.filter { it.adiantamento > 0 }
            val totalPag = kotlin.math.max(1, kotlin.math.ceil(fretesAdiant.size.toDouble() / rowsPerPage).toInt())
            var tA = 0.0
            for (pg in 0 until totalPag) {
                val page = pdf.startPage(PdfDocument.PageInfo.Builder(pageW, pageH, pg).create())
                val c = page.canvas
                c.drawText("Relatorio de Adiantamentos por Forma de Pagamento", margin, 40f, pTitle)
                c.drawText("Gerado em ${df.format(Date())} - Pagina ${pg + 1} de $totalPag", margin, 58f, pSub)
                c.drawLine(margin, 70f, pageW - margin, 70f, pBord)
                c.drawRect(margin, headerY - 12f, pageW - margin, headerY + 4f, pBgH)
                headers.forEachIndexed { i, h -> c.drawText(h, colX[i], headerY, pHead) }
                val ini = pg * rowsPerPage
                val fim = kotlin.math.min(ini + rowsPerPage, fretesAdiant.size)
                var y = headerY + rowH
                for (idx in ini until fim) {
                    val f = fretesAdiant[idx]
                    if ((idx - ini) % 2 == 1) c.drawRect(margin, y - 10f, pageW - margin, y + 6f, pBgA)
                    c.drawText(f.data, colX[0], y, pCell)
                    c.drawText(f.placa, colX[1], y, pCell)
                    c.drawText(f.transportadora.ifBlank { "-" }, colX[2], y, pCell)
                    c.drawText("${f.origem.ifBlank{"-"}} -> ${f.destino.ifBlank{"-"}}".take(18), colX[3], y, pCell)
                    c.drawText(f.formaPgtoAdiant, colX[4], y, pCell)
                    c.drawText(nf.format(f.adiantamento), colX[5], y, pBold)
                    tA += f.adiantamento
                    y += rowH
                }
                c.drawRect(margin, headerY - 12f, pageW - margin, y, pBord)
                if (pg == totalPag - 1) {
                    val ty = y + 25f
                    c.drawText("RESUMO POR FORMA DE PAGAMENTO:", margin, ty, pTot)
                    var yPos = ty + 20f
                    resumo.forEach { r ->
                        c.drawText("${r.formaPagto}: ${r.totalFretes}x ${nf.format(r.totalValor)}", margin, yPos, pCell)
                        yPos += 16f
                    }
                    c.drawText("TOTAL GERAL: ${nf.format(tA)}", margin, yPos + 10f, pTot)
                }
                pdf.finishPage(page)
            }
            val fileName = "GerFrota_Adiantamentos_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale("pt","BR")).format(Date())}.pdf"
            val folder = File(context.filesDir, "relatorios").apply { if (!exists()) mkdirs() }
            val file = File(folder, fileName)
            FileOutputStream(file).use { out -> pdf.writeTo(out) }
            pdf.close()
            PdfResult(true, "Relatorio de adiantamentos gerado!", FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file))
        }.getOrElse { PdfResult(false, "Erro: ${it.message}") }
    }
    suspend fun exportarSaldoPorForma(context: Context, resumo: List<ResumoFormaPagto>, fretes: List<FreteEntity>): PdfResult = withContext(Dispatchers.IO) {
        runCatching {
            val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
            val df = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale("pt", "BR"))
            val pdf = PdfDocument()
            val pageW = 595; val pageH = 842; val margin = 30f
            val pTitle = Paint().apply { color = Color.parseColor("#0D47A1"); textSize = 20f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pSub = Paint().apply { color = Color.parseColor("#1976D2"); textSize = 11f; isAntiAlias = true }
            val pHead = Paint().apply { color = Color.WHITE; textSize = 9f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pCell = Paint().apply { color = Color.BLACK; textSize = 8f; isAntiAlias = true }
            val pBold = Paint().apply { color = Color.BLACK; textSize = 8f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pBgH = Paint().apply { color = Color.parseColor("#F44336") }
            val pBgA = Paint().apply { color = Color.parseColor("#F5F5F5") }
            val pBord = Paint().apply { color = Color.parseColor("#BDBDBD"); style = Paint.Style.STROKE; strokeWidth = 0.5f }
            val pTot = Paint().apply { color = Color.parseColor("#0D47A1"); textSize = 12f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val colX = floatArrayOf(margin, margin + 60, margin + 120, margin + 200, margin + 280, margin + 360, margin + 440)
            val headers = arrayOf("Data", "Placa", "Transportadora", "Rota", "Forma Pgto", "Saldo")
            val rowH = 16f; val headerY = 100f; val rowsPerPage = 40
            val fretesSaldo = fretes.filter { it.saldoFrete > 0 && !it.recebido }
            val totalPag = kotlin.math.max(1, kotlin.math.ceil(fretesSaldo.size.toDouble() / rowsPerPage).toInt())
            var tS = 0.0
            for (pg in 0 until totalPag) {
                val page = pdf.startPage(PdfDocument.PageInfo.Builder(pageW, pageH, pg).create())
                val c = page.canvas
                c.drawText("Relatorio de Saldo a Receber por Forma de Pagamento", margin, 40f, pTitle)
                c.drawText("Gerado em ${df.format(Date())} - Pagina ${pg + 1} de $totalPag", margin, 58f, pSub)
                c.drawLine(margin, 70f, pageW - margin, 70f, pBord)
                c.drawRect(margin, headerY - 12f, pageW - margin, headerY + 4f, pBgH)
                headers.forEachIndexed { i, h -> c.drawText(h, colX[i], headerY, pHead) }
                val ini = pg * rowsPerPage
                val fim = kotlin.math.min(ini + rowsPerPage, fretesSaldo.size)
                var y = headerY + rowH
                for (idx in ini until fim) {
                    val f = fretesSaldo[idx]
                    if ((idx - ini) % 2 == 1) c.drawRect(margin, y - 10f, pageW - margin, y + 6f, pBgA)
                    c.drawText(f.data, colX[0], y, pCell)
                    c.drawText(f.placa, colX[1], y, pCell)
                    c.drawText(f.transportadora.ifBlank { "-" }, colX[2], y, pCell)
                    c.drawText("${f.origem.ifBlank{"-"}} -> ${f.destino.ifBlank{"-"}}".take(18), colX[3], y, pCell)
                    c.drawText(f.formaPgtoSaldo, colX[4], y, pCell)
                    c.drawText(nf.format(f.saldoFrete), colX[5], y, pBold)
                    tS += f.saldoFrete
                    y += rowH
                }
                c.drawRect(margin, headerY - 12f, pageW - margin, y, pBord)
                if (pg == totalPag - 1) {
                    val ty = y + 25f
                    c.drawText("RESUMO POR FORMA DE PAGAMENTO:", margin, ty, pTot)
                    var yPos = ty + 20f
                    resumo.forEach { r ->
                        c.drawText("${r.formaPagto}: ${r.totalFretes}x ${nf.format(r.totalValor)}", margin, yPos, pCell)
                        yPos += 16f
                    }
                    c.drawText("TOTAL GERAL A RECEBER: ${nf.format(tS)}", margin, yPos + 10f, pTot)
                }
                pdf.finishPage(page)
            }
            val fileName = "GerFrota_Saldo_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale("pt","BR")).format(Date())}.pdf"
            val folder = File(context.filesDir, "relatorios").apply { if (!exists()) mkdirs() }
            val file = File(folder, fileName)
            FileOutputStream(file).use { out -> pdf.writeTo(out) }
            pdf.close()
            PdfResult(true, "Relatorio de saldo gerado!", FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file))
        }.getOrElse { PdfResult(false, "Erro: ${it.message}") }
    }
}
'''

# 15. DriveBackupManager.kt
# 15. DriveBackupManager.kt
A["app/src/main/java/com/gerfrota/fretes/drive/DriveBackupManager.kt"] = r'''package com.gerfrota.fretes.drive

import android.accounts.AccountManager
import android.content.Context
import com.google.api.client.googleapis.extensions.android.gms.auth.GoogleAccountCredential
import com.google.api.client.http.InputStreamContent
import com.google.api.client.http.javanet.NetHttpTransport
import com.google.api.client.json.gson.GsonFactory
import com.google.api.services.drive.Drive
import com.google.api.services.drive.DriveScopes
import com.google.api.services.drive.model.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.FileInputStream

class DriveBackupManager(private val context: Context) {
    private fun getGoogleAccount(): String? {
        val am = AccountManager.get(context)
        return am.getAccountsByType("com.google").firstOrNull()?.name
    }

    private fun buildDrive(accountEmail: String): Drive {
        val credential = GoogleAccountCredential.usingOAuth2(context, listOf(DriveScopes.DRIVE_FILE))
            .apply { selectedAccountName = accountEmail }
        return Drive.Builder(NetHttpTransport(), GsonFactory.getDefaultInstance(), credential)
            .setApplicationName("GerFrotaFretes").build()
    }

    suspend fun uploadBackupParaDrive(backupPath: String): BackupDriveResult = withContext(Dispatchers.IO) {
        runCatching {
            val accountEmail = getGoogleAccount() ?: return@withContext BackupDriveResult.Error("Nenhuma conta Google no dispositivo.")
            val drive = buildDrive(accountEmail)
            val backupFile = java.io.File(backupPath)
            
            val fileInputStream = FileInputStream(backupFile)
            val mediaContent = InputStreamContent("application/json", fileInputStream)
            
            val metadata = File().apply { 
                name = "gerfrota_backup_${System.currentTimeMillis()}.json"
                mimeType = "application/json" 
            }
            
            val query = "name contains 'gerfrota_backup' and mimeType='application/json' and trashed=false"
            val existing = drive.files().list().setQ(query).setSpaces("drive").setFields("files(id, name)").execute()
            
            if (existing.files.isNullOrEmpty()) {
                drive.files().create(metadata, mediaContent).setFields("id").execute()
            } else {
                val fileId = existing.files[0].id
                drive.files().update(fileId, metadata, mediaContent).execute()
            }
            fileInputStream.close()
            BackupDriveResult.Sucesso("Backup enviado para Drive ($accountEmail)")
        }.getOrElse { BackupDriveResult.Error("Erro no upload: ${it.message}") }
    }

    suspend fun downloadBackupDoDrive(): BackupDriveResult = withContext(Dispatchers.IO) {
        runCatching {
            val accountEmail = getGoogleAccount() ?: return@withContext BackupDriveResult.Error("Nenhuma conta Google no dispositivo.")
            val drive = buildDrive(accountEmail)
            val query = "name contains 'gerfrota_backup' and mimeType='application/json' and trashed=false"
            val files = drive.files().list().setQ(query).setSpaces("drive").setFields("files(id, name)").orderBy("createdTime desc").execute()
            
            if (files.files.isNullOrEmpty()) return@withContext BackupDriveResult.Error("Nenhum backup encontrado no Drive.")
            
            val fileId = files.files[0].id
            
            // ✅ CORREÇÃO: O método correto da API do Google Drive é executeMediaAsInputStream()
            val inputStream = drive.files().get(fileId).executeMediaAsInputStream()
            
            val backupDir = context.filesDir.resolve("backups").apply { if (!exists()) mkdirs() }
            val backupFile = backupDir.resolve("gerfrota_backup_downloaded.json")
            
            backupFile.outputStream().use { it.write(inputStream.readBytes()) }
            inputStream.close()
            
            BackupDriveResult.Sucesso("Backup baixado do Drive: ${backupFile.absolutePath}")
        }.getOrElse { BackupDriveResult.Error("Erro no download: ${it.message}") }
    }
}

sealed class BackupDriveResult {
    data class Sucesso(val message: String) : BackupDriveResult()
    data class Error(val message: String) : BackupDriveResult()
}
'''

# 16. LoginScreen.kt
A["app/src/main/java/com/gerfrota/fretes/ui/LoginScreen.kt"] = r'''package com.gerfrota.fretes.ui
import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.gerfrota.fretes.R
import com.gerfrota.fretes.data.AuthManager
import com.gerfrota.fretes.data.LoginResult
import com.gerfrota.fretes.data.Repository
@Composable
fun LoginScreen(repo: Repository, onLoginSuccess: () -> Unit) {
    val context = LocalContext.current
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var isRegisterMode by remember { mutableStateOf(!AuthManager.isRegistered(context)) }
    var loading by remember { mutableStateOf(false) }
    Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.primary) {
        Column(modifier = Modifier.fillMaxSize().padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Image(painter = painterResource(R.drawable.ic_truck_logo), contentDescription = null, modifier = Modifier.size(140.dp))
            Spacer(Modifier.height(20.dp))
            Text("GerFrota Fretes", fontSize = 30.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onPrimary, textAlign = TextAlign.Center)
            Text(if (isRegisterMode) "Crie sua conta" else "Entre com sua conta", fontSize = 15.sp, color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.85f))
            Spacer(Modifier.height(32.dp))
            Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
                Column(Modifier.padding(20.dp)) {
                    OutlinedTextField(value = email, onValueChange = { email = it }, label = { Text("E-mail") }, leadingIcon = { Icon(Icons.Default.Email, null) },
                        modifier = Modifier.fillMaxWidth(), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email), singleLine = true)
                    Spacer(Modifier.height(12.dp))
                    OutlinedTextField(value = password, onValueChange = { password = it }, label = { Text("Senha") }, leadingIcon = { Icon(Icons.Default.Lock, null) },
                        modifier = Modifier.fillMaxWidth(), visualTransformation = PasswordVisualTransformation(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password), singleLine = true)
                    if (isRegisterMode) {
                        Spacer(Modifier.height(12.dp))
                        OutlinedTextField(value = confirmPassword, onValueChange = { confirmPassword = it }, label = { Text("Confirmar senha") }, leadingIcon = { Icon(Icons.Default.Lock, null) },
                            modifier = Modifier.fillMaxWidth(), visualTransformation = PasswordVisualTransformation(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password), singleLine = true)
                    }
                    Spacer(Modifier.height(20.dp))
                    Button(onClick = {
                        if (loading) return@Button
                        loading = true
                        if (isRegisterMode) {
                            if (password != confirmPassword) { Toast.makeText(context, "As senhas nao conferem", Toast.LENGTH_SHORT).show(); loading = false; return@Button }
                            if (AuthManager.registrar(context, email, password)) { Toast.makeText(context, "Conta criada!", Toast.LENGTH_SHORT).show(); onLoginSuccess() }
                            else { Toast.makeText(context, "Preencha e-mail e senha (min. 4)", Toast.LENGTH_SHORT).show() }
                        } else {
                            when (AuthManager.login(context, email, password)) {
                                LoginResult.SUCCESS -> onLoginSuccess()
                                LoginResult.WRONG_EMAIL -> Toast.makeText(context, "E-mail nao cadastrado", Toast.LENGTH_SHORT).show()
                                LoginResult.WRONG_PASSWORD -> Toast.makeText(context, "Senha incorreta", Toast.LENGTH_SHORT).show()
                                LoginResult.NOT_REGISTERED -> { isRegisterMode = true; Toast.makeText(context, "Crie uma conta", Toast.LENGTH_SHORT).show() }
                            }
                        }
                        loading = false
                    }, modifier = Modifier.fillMaxWidth().height(52.dp), shape = RoundedCornerShape(12.dp), enabled = !loading) {
                        if (loading) CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                        else Text(if (isRegisterMode) "CRIAR CONTA" else "ENTRAR", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    }
                    if (AuthManager.isRegistered(context)) {
                        Spacer(Modifier.height(8.dp))
                        TextButton(onClick = { isRegisterMode = !isRegisterMode }, modifier = Modifier.fillMaxWidth()) {
                            Text(if (isRegisterMode) "Ja tenho conta - Entrar" else "Nao tenho conta - Criar agora", fontSize = 13.sp)
                        }
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
            Text("Seus dados ficam salvos no dispositivo", fontSize = 12.sp, color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f), textAlign = TextAlign.Center)
        }
    }
}
'''

# 17. HomeScreen.kt
A["app/src/main/java/com/gerfrota/fretes/ui/HomeScreen.kt"] = r'''package com.gerfrota.fretes.ui
import android.content.Intent
import android.widget.Toast
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.gerfrota.fretes.data.FreteEntity
import com.gerfrota.fretes.data.PdfExporter
import com.gerfrota.fretes.data.Repository
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.Locale
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(repo: Repository, userEmail: String, onAddClick: () -> Unit, onEditClick: (FreteEntity) -> Unit,
    onPlacasClick: () -> Unit, onFretesClick: () -> Unit, onRelatoriosClick: () -> Unit, onBackupClick: () -> Unit, onLogout: () -> Unit) {
    val fretes by repo.fretes.collectAsState(initial = emptyList())
    val saldoTotal by repo.saldoTotal.collectAsState(initial = 0.0)
    val scope = rememberCoroutineScope()
    val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
    val context = LocalContext.current
    var menuOpen by remember { mutableStateOf(false) }
    var filtroTransportadora by remember { mutableStateOf<String?>(null) }
    var filtroPlaca by remember { mutableStateOf<String?>(null) }
    val transportadoras by repo.transportadoras.collectAsState(initial = emptyList())
    val placas by repo.placasLista.collectAsState(initial = emptyList())
    val fretesFiltrados = fretes.filter { f ->
        (filtroTransportadora == null || f.transportadora == filtroTransportadora) && (filtroPlaca == null || f.placa == filtroPlaca)
    }
    Scaffold(
        topBar = {
            TopAppBar(title = { Column {
                Text(text = "GerFrota Fretes", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Text(text = "Sistema de Gestão de Fretes", fontSize = 10.sp, color = Color.White.copy(alpha = 0.8f))
            } }, actions = {
                IconButton(onClick = { menuOpen = true }) { Icon(Icons.Default.MoreVert, "Menu", tint = Color.White) }
                DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                    DropdownMenuItem(text = { Text(text = "📊 Relatorios") }, onClick = { menuOpen = false; onRelatoriosClick() }, leadingIcon = { Icon(Icons.Default.PictureAsPdf, null) })
                    DropdownMenuItem(text = { Text(text = "💾 Backup") }, onClick = { menuOpen = false; onBackupClick() }, leadingIcon = { Icon(Icons.Default.CloudUpload, null) })
                    DropdownMenuItem(text = { Text(text = "Sair") }, onClick = { menuOpen = false; onLogout() }, leadingIcon = { Icon(Icons.Default.Logout, null) })
                }
            })
        },
        floatingActionButton = { FloatingActionButton(onClick = onAddClick) { Icon(Icons.Default.Add, "Novo Frete") } }
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Card(modifier = Modifier.weight(1f).clickable { onRelatoriosClick() }, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primary)) {
                    Column(Modifier.padding(16.dp)) { Text(text = "GerFrota Fretes", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        Text(text = "Gestão Completa", fontSize = 11.sp, color = Color.White.copy(alpha = 0.8f)) }
                }
                Card(modifier = Modifier.weight(1f).clickable { onPlacasClick() }, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondary)) {
                    Column(Modifier.padding(16.dp)) { Text(text = "Placas", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        Text(text = "${placas.size} veículos", fontSize = 11.sp, color = Color.White.copy(alpha = 0.8f)) }
                }
            }
            Card(modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp).clickable { onFretesClick() }, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiary)) {
                Row(Modifier.padding(16.dp).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Column { Text(text = "Fretes", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        Text(text = "${fretes.size} registros", fontSize = 11.sp, color = Color.White.copy(alpha = 0.8f)) }
                    Icon(Icons.Default.LocalShipping, null, tint = Color.White)
                }
            }
            Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                var showTranspFilter by remember { mutableStateOf(false) }
                ExposedDropdownMenuBox(filtroTransportadora != null, onExpandedChange = { showTranspFilter = it }) {
                    OutlinedTextField(value = filtroTransportadora ?: "Todas Transportadoras", onValueChange = {}, modifier = Modifier.weight(1f).menuAnchor(), readOnly = true, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(showTranspFilter) })
                    ExposedDropdownMenu(showTranspFilter, onDismissRequest = { showTranspFilter = false }) {
                        DropdownMenuItem(text = { Text("Todas Transportadoras") }, onClick = { filtroTransportadora = null; showTranspFilter = false })
                        transportadoras.forEach { transp -> DropdownMenuItem(text = { Text(transp) }, onClick = { filtroTransportadora = transp; showTranspFilter = false }) }
                    }
                }
                var showPlacaFilter by remember { mutableStateOf(false) }
                ExposedDropdownMenuBox(filtroPlaca != null, onExpandedChange = { showPlacaFilter = it }) {
                    OutlinedTextField(value = filtroPlaca ?: "Todas Placas", onValueChange = {}, modifier = Modifier.weight(1f).menuAnchor(), readOnly = true, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(showPlacaFilter) })
                    ExposedDropdownMenu(showPlacaFilter, onDismissRequest = { showPlacaFilter = false }) {
                        DropdownMenuItem(text = { Text("Todas Placas") }, onClick = { filtroPlaca = null; showPlacaFilter = false })
                        placas.forEach { placa -> DropdownMenuItem(text = { Text(placa) }, onClick = { filtroPlaca = placa; showPlacaFilter = false }) }
                    }
                }
            }
            Card(modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
                Column(Modifier.padding(16.dp)) {
                    Text(text = "SALDO A RECEBER", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onErrorContainer)
                    Text(text = nf.format(saldoTotal ?: 0.0).toString(), fontSize = 28.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onErrorContainer)
                    if (filtroTransportadora != null || filtroPlaca != null) Text(text = "Filtrado", fontSize = 11.sp, color = MaterialTheme.colorScheme.onErrorContainer.copy(alpha = 0.7f))
                }
            }
            Text(text = "  Fretes Recentes", fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
            LazyColumn(Modifier.padding(horizontal = 16.dp)) {
                items(fretesFiltrados) { f ->
                    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Column(Modifier.padding(12.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(text = f.transportadora.ifBlank { "Sem transportadora" }, fontWeight = FontWeight.Bold, fontSize = 14.sp, modifier = Modifier.weight(1f))
                                Text(text = nf.format(f.saldoFrete).toString(), fontWeight = FontWeight.Bold, color = if (f.recebido) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
                            }
                            Text(text = "${f.origem} -> ${f.destino}", fontSize = 12.sp, color = Color.Gray)
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(text = "${f.data} - ${f.placa}", fontSize = 11.sp, color = Color.Gray)
                                TextButton(onClick = { onEditClick(f) }) { Text(text = "Editar", fontSize = 11.sp, color = MaterialTheme.colorScheme.primary) }
                            }
                            if (f.recebido) Text(text = "RECEBIDO", fontSize = 10.sp, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }
    }
}
'''

# 18. PlacasScreen.kt
A["app/src/main/java/com/gerfrota/fretes/ui/PlacasScreen.kt"] = r'''package com.gerfrota.fretes.ui
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.gerfrota.fretes.data.FreteEntity
import com.gerfrota.fretes.data.PlacaResumo
import com.gerfrota.fretes.data.Repository
import java.text.NumberFormat
import java.util.Locale
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlacasScreen(repo: Repository, onBack: () -> Unit) {
    val resumo by repo.resumoPorPlaca.collectAsState(initial = emptyList())
    val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
    var placaSelecionada by remember { mutableStateOf<String?>(null) }
    Scaffold(topBar = { TopAppBar(title = { Text(text = if (placaSelecionada == null) "Fretes por Placa" else placaSelecionada!!) },
        navigationIcon = { IconButton(onClick = { if (placaSelecionada != null) placaSelecionada = null else onBack() }) { Icon(Icons.Default.ArrowBack, "Voltar") } } ) }) { padding ->
        if (placaSelecionada == null) {
            Column(Modifier.padding(padding).fillMaxSize()) {
                val totalGeral = resumo.sumOf { it.totalSaldo }
                val fretesTotal = resumo.sumOf { it.totalFretes }
                Card(modifier = Modifier.fillMaxWidth().padding(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primary)) {
                    Column(Modifier.padding(20.dp).fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "TOTAL GERAL - TODAS AS PLACAS", color = Color.White.copy(alpha = 0.85f), fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        Text(text = nf.format(totalGeral).toString(), color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                        Text(text = "$fretesTotal fretes cadastrados", color = Color.White.copy(alpha = 0.8f), fontSize = 12.sp)
                    }
                }
                LazyColumn(Modifier.padding(horizontal = 16.dp)) { items(resumo) { r -> CardPlaca(r, nf) { placaSelecionada = r.placa } } }
            }
        } else {
            val fretes by repo.fretesPorPlaca(placaSelecionada!!).collectAsState(initial = emptyList())
            LazyColumn(Modifier.padding(padding).padding(horizontal = 16.dp)) { items(fretes) { f -> FreteItemPlaca(f, nf) } }
        }
    }
}
@Composable
fun CardPlaca(resumo: PlacaResumo, nf: NumberFormat, onClick: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp).clickable { onClick() }, elevation = CardDefaults.cardElevation(3.dp)) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.LocalShipping, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(32.dp))
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) { Text(text = resumo.placa, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Text(text = "${resumo.totalFretes} fretes", fontSize = 12.sp, color = Color.Gray) }
                Text(text = nf.format(resumo.totalSaldo).toString(), fontWeight = FontWeight.Bold, fontSize = 16.sp,
                    color = if (resumo.totalSaldo > 0) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary)
            }
        }
    }
}
@Composable
fun FreteItemPlaca(f: FreteEntity, nf: NumberFormat) {
    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Column(Modifier.padding(12.dp)) {
            Text(text = f.transportadora.ifBlank { "Sem transportadora" }, fontWeight = FontWeight.Bold)
            Text(text = "${f.origem} -> ${f.destino}", fontSize = 12.sp, color = Color.Gray)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(text = "${f.data}", fontSize = 11.sp, color = Color.Gray)
                Text(text = nf.format(f.saldoFrete).toString(), fontWeight = FontWeight.Bold)
            }
        }
    }
}
'''

# 19. RelatoriosScreen.kt
A["app/src/main/java/com/gerfrota/fretes/ui/RelatoriosScreen.kt"] = r'''package com.gerfrota.fretes.ui
import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.gerfrota.fretes.data.PdfExporter
import com.gerfrota.fretes.data.Repository
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.*
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RelatoriosScreen(repo: Repository, onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val fretes by repo.fretes.collectAsState(initial = emptyList())
    val fretesNaoRecebidos by repo.fretesNaoRecebidos.collectAsState(initial = emptyList())
    val totalAdiant by repo.totalAdiantamentos.collectAsState(initial = 0.0)
    val resumoAdiant by repo.resumoAdiantamentoPorForma.collectAsState(initial = emptyList())
    val resumoSaldo by repo.resumoSaldoPorForma.collectAsState(initial = emptyList())
    var gerando by remember { mutableStateOf(false) }
    var tipoRelatorio by remember { mutableStateOf("total") }
    val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
    Scaffold(topBar = { TopAppBar(title = { Text(text = "Relatorios") }, navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Voltar") } }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState())) {
            Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                Column(Modifier.padding(16.dp)) { Text(text = "Relatorios PDF", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    Text(text = "Escolha o tipo e gere em PDF", fontSize = 12.sp) }
            }
            Spacer(Modifier.height(16.dp))
            Text(text = "Tipo de Relatorio", fontWeight = FontWeight.Bold)
            Row(Modifier.fillMaxWidth().padding(vertical = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(selected = tipoRelatorio == "total", onClick = { tipoRelatorio = "total" }, label = { Text(text = "Total") })
                FilterChip(selected = tipoRelatorio == "periodo", onClick = { tipoRelatorio = "periodo" }, label = { Text(text = "Periodo") })
                FilterChip(selected = tipoRelatorio == "adiant_forma", onClick = { tipoRelatorio = "adiant_forma" }, label = { Text(text = "Adiant. por Forma") })
                FilterChip(selected = tipoRelatorio == "saldo_forma", onClick = { tipoRelatorio = "saldo_forma" }, label = { Text(text = "Saldo por Forma") })
            }
            Spacer(Modifier.height(16.dp))
            Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                Column(Modifier.padding(16.dp)) {
                    Text(text = "Resumo Geral", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Spacer(Modifier.height(8.dp))
                    Text(text = "Total de fretes: ${fretes.size}", fontSize = 12.sp)
                    Text(text = "Fretes nao recebidos: ${fretesNaoRecebidos.size}", fontSize = 12.sp)
                    Text(text = "Total adiantamentos: ${nf.format(totalAdiant ?: 0.0)}", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
            if (tipoRelatorio == "adiant_forma") {
                Spacer(Modifier.height(16.dp))
                Text(text = "Adiantamentos por Forma de Pagamento", fontWeight = FontWeight.Bold)
                if (resumoAdiant.isEmpty()) Text(text = "Nenhum adiantamento registrado", color = Color.Gray, modifier = Modifier.padding(8.dp))
                else { resumoAdiant.forEach { r -> Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Row(Modifier.padding(12.dp).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(text = r.formaPagto, fontWeight = FontWeight.Bold)
                        Text(text = "${r.totalFretes}x ${nf.format(r.totalValor)}", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                    }}}}
            }
            if (tipoRelatorio == "saldo_forma") {
                Spacer(Modifier.height(16.dp))
                Text(text = "Saldo a Receber por Forma de Pagamento", fontWeight = FontWeight.Bold)
                if (resumoSaldo.isEmpty()) Text(text = "Nenhum saldo pendente", color = Color.Gray, modifier = Modifier.padding(8.dp))
                else { resumoSaldo.forEach { r -> Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Row(Modifier.padding(12.dp).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(text = r.formaPagto, fontWeight = FontWeight.Bold)
                        Text(text = "${r.totalFretes}x ${nf.format(r.totalValor)}", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.error)
                    }}}}
            }
            Spacer(Modifier.height(24.dp))
            Button(onClick = {
                if (gerando) return@Button
                gerando = true
                scope.launch {
                    val resultado = when (tipoRelatorio) {
                        "adiant_forma" -> PdfExporter.exportarAdiantamentoPorForma(context, resumoAdiant, fretes)
                        "saldo_forma" -> PdfExporter.exportarSaldoPorForma(context, resumoSaldo, fretes)
                        else -> PdfExporter.exportar(context, fretes, "Relatorio Completo")
                    }
                    gerando = false
                    Toast.makeText(context, if (resultado.success) "Relatorio gerado!" else resultado.message, Toast.LENGTH_LONG).show()
                }
            }, modifier = Modifier.fillMaxWidth().height(56.dp), enabled = !gerando) {
                if (gerando) CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                else { Icon(Icons.Default.PictureAsPdf, null); Spacer(Modifier.width(8.dp)); Text(text = "GERAR RELATORIO PDF", fontSize = 16.sp, fontWeight = FontWeight.Bold) }
            }
        }
    }
}
'''

# 20. BackupScreen.kt
A["app/src/main/java/com/gerfrota/fretes/ui/BackupScreen.kt"] = r'''package com.gerfrota.fretes.ui
import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.gerfrota.fretes.data.LocalBackupManager
import com.gerfrota.fretes.data.Repository
import com.gerfrota.fretes.drive.DriveBackupManager
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BackupScreen(repo: Repository, onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val driveManager = remember { DriveBackupManager(context) }
    val fretes by repo.fretes.collectAsState(initial = emptyList())
    var etapa by remember { mutableStateOf(1) }
    var processando by remember { mutableStateOf(false) }
    var mensagem by remember { mutableStateOf("") }
    var backupPath by remember { mutableStateOf<String?>(null) }
    
    Scaffold(topBar = { TopAppBar(title = { Text(text = "Backup - 3 Etapas") }, navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Voltar") } }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState())) {
            Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                Column(Modifier.padding(16.dp)) { Text(text = "Sistema de Backup", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    Text(text = "Siga as 3 etapas para backup completo", fontSize = 12.sp) }
            }
            Spacer(Modifier.height(24.dp))
            
            StepCard(numero = 1, titulo = "Gerar Arquivo de Backup", descricao = "Cria arquivo JSON com todos os fretes", icone = Icons.Default.Save, ativo = etapa == 1,
                acao = { processando = true; scope.launch {
                    val (sucesso, path) = LocalBackupManager.criarBackupLocal(context, fretes)
                    processando = false
                    if (sucesso) { 
                        backupPath = path
                        etapa = 2
                        mensagem = "Backup gerado com sucesso" 
                    } else { 
                        mensagem = "Erro ao gerar backup" 
                    }
                    Toast.makeText(context, if (sucesso) "Backup gerado!" else "Erro", Toast.LENGTH_SHORT).show()
                }}, processando = processando && etapa == 1)
                
            Spacer(Modifier.height(16.dp))
            
            StepCard(numero = 2, titulo = "Upload para Google Drive", descricao = "Envia backup para sua conta Google Drive", icone = Icons.Default.CloudUpload, ativo = etapa == 2,
                habilitado = backupPath != null, acao = { 
                    if (backupPath == null) return@StepCard
                    processando = true
                    scope.launch {
                        val resultado = driveManager.uploadBackupParaDrive(backupPath!!)
                        processando = false
                        
                        // CORREÇÃO: Uso explícito de if/else para garantir o smart-cast e acesso à propriedade .message
                        if (resultado is com.gerfrota.fretes.drive.BackupDriveResult.Sucesso) {
                            etapa = 3
                            mensagem = resultado.message
                            Toast.makeText(context, "Upload concluído!", Toast.LENGTH_LONG).show()
                        } else if (resultado is com.gerfrota.fretes.drive.BackupDriveResult.Error) {
                            mensagem = resultado.message
                            Toast.makeText(context, resultado.message, Toast.LENGTH_LONG).show()
                        }
                    }
                }, processando = processando && etapa == 2)
                
            Spacer(Modifier.height(16.dp))
            
            StepCard(numero = 3, titulo = "Download do Google Drive", descricao = "Baixa backup mais recente do Drive", icone = Icons.Default.CloudDownload, ativo = etapa == 3,
                acao = { processando = true; scope.launch {
                    val resultado = driveManager.downloadBackupDoDrive()
                    processando = false
                    
                    // CORREÇÃO: Uso explícito de if/else para garantir o smart-cast e acesso à propriedade .message
                    if (resultado is com.gerfrota.fretes.drive.BackupDriveResult.Sucesso) {
                        mensagem = resultado.message
                        Toast.makeText(context, "Download concluído!", Toast.LENGTH_LONG).show()
                    } else if (resultado is com.gerfrota.fretes.drive.BackupDriveResult.Error) {
                        mensagem = resultado.message
                        Toast.makeText(context, resultado.message, Toast.LENGTH_LONG).show()
                    }
                }}, processando = processando && etapa == 3)
                
            Spacer(Modifier.height(24.dp))
            if (mensagem.isNotEmpty()) {
                Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = if (etapa == 3) MaterialTheme.colorScheme.secondaryContainer else MaterialTheme.colorScheme.tertiaryContainer)) {
                    Text(text = mensagem, modifier = Modifier.padding(16.dp), fontSize = 12.sp)
                }
            }
            Spacer(Modifier.height(16.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { etapa = 1 }, modifier = Modifier.weight(1f), enabled = etapa > 1) { Text(text = "Reiniciar") }
                Button(onClick = onBack, modifier = Modifier.weight(1f)) { Text(text = "Concluir") }
            }
        }
    }
}

@Composable
fun StepCard(numero: Int, titulo: String, descricao: String, icone: androidx.compose.ui.graphics.vector.ImageVector, ativo: Boolean, acao: () -> Unit, processando: Boolean = false, habilitado: Boolean = true) {
    Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = if (ativo) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant),
        border = if (ativo) androidx.compose.foundation.BorderStroke(2.dp, MaterialTheme.colorScheme.primary) else null) {
        Row(Modifier.padding(16.dp).fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Icon(icone, null, tint = if (ativo) MaterialTheme.colorScheme.primary else Color.Gray, modifier = Modifier.size(40.dp))
            Spacer(Modifier.width(16.dp))
            Column(Modifier.weight(1f)) { Text(text = "Etapa $numero: $titulo", fontWeight = FontWeight.Bold, fontSize = 14.sp); Text(text = descricao, fontSize = 11.sp, color = Color.Gray) }
            Button(onClick = acao, enabled = habilitado && !processando) {
                if (processando) CircularProgressIndicator(modifier = Modifier.size(20.dp), color = MaterialTheme.colorScheme.onPrimary)
                else Text(text = "Executar")
            }
        }
    }
}
'''

# 21. FreteFormScreen.kt
A["app/src/main/java/com/gerfrota/fretes/ui/FreteFormScreen.kt"] = r'''package com.gerfrota.fretes.ui
import android.app.Activity
import android.speech.RecognizerIntent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.gerfrota.fretes.data.*
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FreteFormScreen(repo: Repository, freteParaEditar: FreteEntity? = null, onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    val isEdit = freteParaEditar != null
    var data by remember { mutableStateOf(freteParaEditar?.data ?: SimpleDateFormat("dd/MM/yyyy", Locale("pt","BR")).format(Date())) }
    var placa by remember { mutableStateOf(freteParaEditar?.placa ?: "") }
    var transportadora by remember { mutableStateOf(freteParaEditar?.transportadora ?: "") }
    var origem by remember { mutableStateOf(freteParaEditar?.origem ?: "") }
    var destino by remember { mutableStateOf(freteParaEditar?.destino ?: "") }
    var valorStr by remember { mutableStateOf(freteParaEditar?.valorFrete?.toString() ?: "") }
    var adiantStr by remember { mutableStateOf(freteParaEditar?.adiantamento?.toString() ?: "0") }
    var formaAdiant by remember { mutableStateOf(freteParaEditar?.formaPgtoAdiant ?: FormasPagamento.opcoes.first()) }
    var formaSaldo by remember { mutableStateOf(freteParaEditar?.formaPgtoSaldo ?: FormasPagamento.opcoes.first()) }
    var recebido by remember { mutableStateOf(freteParaEditar?.recebido ?: false) }
    var voiceTarget by remember { mutableStateOf<String?>(null) }
    var salvando by remember { mutableStateOf(false) }
    val voiceLauncher = rememberLauncherForActivityResult(contract = ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val matches = result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
            val spoken = matches?.firstOrNull().orEmpty()
            when (voiceTarget) {
                "valor" -> valorStr = VoiceInputHelper.parseNumber(spoken)
                "adiant" -> adiantStr = VoiceInputHelper.parseNumber(spoken).ifBlank { "0" }
                "transportadora" -> transportadora = spoken
                "origem" -> origem = spoken
                "destino" -> destino = spoken
                "placa" -> placa = spoken
                "data" -> data = spoken
            }
            voiceTarget = null
        }
    }
    fun askVoice(target: String, prompt: String) {
        voiceTarget = target
        val intent = VoiceInputHelper.createIntent().apply { putExtra(RecognizerIntent.EXTRA_PROMPT, prompt) }
        voiceLauncher.launch(intent)
    }
    Scaffold(topBar = { TopAppBar(title = { Text(text = if (isEdit) "Editar Frete" else "Novo Frete") }, navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Voltar") } }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            VoiceField("Data", data, { data = it }, "data", "Fale a data", ::askVoice)
            VoiceField("Transportadora", transportadora, { transportadora = it }, "transportadora", "Fale o nome da transportadora", ::askVoice)
            VoiceField("Origem", origem, { origem = it }, "origem", "Fale a cidade de origem", ::askVoice)
            VoiceField("Destino", destino, { destino = it }, "destino", "Fale a cidade de destino", ::askVoice)
            Text("Placa", style = MaterialTheme.typography.labelMedium)
            val placas by repo.placasLista.collectAsState(initial = emptyList())
            var expanded by remember { mutableStateOf(false) }
            ExposedDropdownMenuBox(expanded, onExpandedChange = { expanded = it }) {
                OutlinedTextField(value = placa, onValueChange = { placa = it }, modifier = Modifier.menuAnchor().fillMaxWidth(), trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) })
                ExposedDropdownMenu(expanded, onDismissRequest = { expanded = false }) {
                    if (placas.isEmpty()) DropdownMenuItem(text = { Text(text = "Nenhuma placa cadastrada", color = Color.Gray) }, onClick = {})
                    else placas.forEach { p -> DropdownMenuItem(text = { Text(p) }, onClick = { placa = p; expanded = false }) }
                }
            }
            VoiceField("Valor do Frete (R$)", valorStr, { valorStr = it }, "valor", "Fale o valor", ::askVoice, KeyboardType.Decimal)
            VoiceField("Adiantamento (R$)", adiantStr, { adiantStr = it }, "adiant", "Fale o adiantamento", ::askVoice, KeyboardType.Decimal)
            Text("Forma Pagto Adiantamento", style = MaterialTheme.typography.labelMedium)
            var exp1 by remember { mutableStateOf(false) }
            ExposedDropdownMenuBox(exp1, onExpandedChange = { exp1 = it }) {
                OutlinedTextField(value = formaAdiant, onValueChange = {}, modifier = Modifier.menuAnchor().fillMaxWidth(), readOnly = true, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(exp1) })
                ExposedDropdownMenu(exp1, onDismissRequest = { exp1 = false }) { FormasPagamento.opcoes.forEach { o -> DropdownMenuItem(text = { Text(o) }, onClick = { formaAdiant = o; exp1 = false }) } }
            }
            Text("Forma Pagto Saldo", style = MaterialTheme.typography.labelMedium)
            var exp2 by remember { mutableStateOf(false) }
            ExposedDropdownMenuBox(exp2, onExpandedChange = { exp2 = it }) {
                OutlinedTextField(value = formaSaldo, onValueChange = {}, modifier = Modifier.menuAnchor().fillMaxWidth(), readOnly = true, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(exp2) })
                ExposedDropdownMenu(exp2, onDismissRequest = { exp2 = false }) { FormasPagamento.opcoes.forEach { o -> DropdownMenuItem(text = { Text(o) }, onClick = { formaSaldo = o; exp2 = false }) } }
            }
            Row(verticalAlignment = Alignment.CenterVertically) { Checkbox(checked = recebido, onCheckedChange = { recebido = it }); Text(text = "Recebido (diminui saldo)", fontWeight = FontWeight.Bold) }
            if (recebido) Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                Text(text = "Ao marcar como recebido, o saldo será zerado", modifier = Modifier.padding(12.dp), fontSize = 12.sp)
            }
            Spacer(Modifier.height(16.dp))
            val valor = valorStr.toDoubleOrNull() ?: 0.0
            val adiant = adiantStr.toDoubleOrNull() ?: 0.0
            val saldo = if (recebido) 0.0 else (valor - adiant)
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                Row(Modifier.padding(16.dp).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(text = "Saldo do Frete:", fontWeight = FontWeight.Bold)
                    Text(text = NumberFormat.getCurrencyInstance(Locale("pt","BR")).format(saldo).toString(), fontWeight = FontWeight.Bold, color = if (recebido) Color.Green else MaterialTheme.colorScheme.primary)
                }
            }
            Button(onClick = {
                if (salvando) return@Button
                salvando = true
                scope.launch {
                    val entity = FreteEntity(id = freteParaEditar?.id ?: 0, data = data, placa = placa, valorFrete = valor, adiantamento = adiant, formaPgtoAdiant = formaAdiant,
                        saldoFrete = saldo, formaPgtoSaldo = formaSaldo, recebido = recebido, transportadora = transportadora, origem = origem, destino = destino)
                    if (isEdit) repo.update(entity) else repo.insert(entity)
                    onBack()
                }
            }, modifier = Modifier.fillMaxWidth().height(56.dp), enabled = !salvando) {
                Text(text = if (isEdit) "ATUALIZAR FRETE" else "SALVAR FRETE", fontSize = 16.sp)
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}
@Composable
fun VoiceField(label: String, value: String, onChange: (String) -> Unit, voiceKey: String, voicePrompt: String, askVoice: (String, String) -> Unit, keyboard: KeyboardType = KeyboardType.Text) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        OutlinedTextField(value = value, onValueChange = onChange, label = { Text(text = label) }, modifier = Modifier.weight(1f), keyboardOptions = KeyboardOptions(keyboardType = keyboard))
        Spacer(Modifier.width(8.dp))
        IconButton(onClick = { askVoice(voiceKey, voicePrompt) }, modifier = Modifier.size(48.dp)) { Icon(Icons.Default.Mic, "Falar", tint = MaterialTheme.colorScheme.primary) }
    }
}
'''

# 22. SaldoReceberScreen.kt
A["app/src/main/java/com/gerfrota/fretes/ui/SaldoReceberScreen.kt"] = r'''package com.gerfrota.fretes.ui
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.gerfrota.fretes.data.Repository
import java.text.NumberFormat
import java.util.Locale
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SaldoReceberScreen(repo: Repository, onBack: () -> Unit) {
    val lista by repo.saldoPorTransportadora.collectAsState(initial = emptyList())
    val total by repo.saldoTotal.collectAsState(initial = 0.0)
    val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
    Scaffold(topBar = { TopAppBar(title = { Text(text = "Saldo a Receber") }, navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Voltar") } }) }) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            Card(modifier = Modifier.fillMaxWidth().padding(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primary)) {
                Column(Modifier.padding(20.dp).fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(text = "TOTAL GERAL A RECEBER", color = Color.White.copy(alpha = 0.85f), fontWeight = FontWeight.Bold)
                    Text(text = nf.format(total ?: 0.0).toString(), color = Color.White, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                }
            }
            Text(text = "  Por Transportadora", fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
            LazyColumn(Modifier.padding(horizontal = 16.dp)) {
                items(lista) { item ->
                    Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Row(Modifier.padding(16.dp).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                            Text(text = item.transportadora.ifBlank { "(sem nome)" }, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                            Text(text = nf.format(item.total).toString(), fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.error, fontSize = 18.sp)
                        }
                    }
                }
            }
        }
    }
}
'''

# 23. VoiceInputHelper.kt
A["app/src/main/java/com/gerfrota/fretes/ui/VoiceInputHelper.kt"] = r'''package com.gerfrota.fretes.ui
import android.content.Intent
import android.speech.RecognizerIntent
import java.util.Locale
object VoiceInputHelper {
    fun createIntent(): Intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale("pt", "BR"))
        putExtra(RecognizerIntent.EXTRA_PROMPT, "Fale o valor...")
        putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
    }
    fun parseNumber(text: String): String {
        val cleaned = text.lowercase(Locale("pt","BR")).replace("reais", "").replace("real", "").replace("virgula", ",").replace("ponto", ".").trim()
        val regex = Regex("[0-9]+([.,][0-9]+)?")
        return regex.find(cleaned)?.value ?: cleaned
    }
}
'''

# 24. MainActivity.kt
A["app/src/main/java/com/gerfrota/fretes/MainActivity.kt"] = r'''package com.gerfrota.fretes
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize // <-- CORREÇÃO AQUI
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.gerfrota.fretes.data.AppDatabase
import com.gerfrota.fretes.data.AuthManager
import com.gerfrota.fretes.data.Repository
import com.gerfrota.fretes.ui.*

class MainActivity : ComponentActivity() {
    private val repo by lazy {
        val db = AppDatabase.get(this)
        Repository(db.freteDao(), db.placaDao())
    }
    private val freteEditTarget = mutableStateOf<Long?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                val nav = rememberNavController()
                var loggedEmail by remember { mutableStateOf<String?>(null) }
                
                LaunchedEffect(Unit) {
                    if (AuthManager.isLogged(this@MainActivity)) {
                        loggedEmail = AuthManager.getEmail(this@MainActivity)
                        nav.navigate("home") { popUpTo("login") { inclusive = true } }
                    }
                }
                
                NavHost(nav, startDestination = "login") {
                    composable("login") {
                        LoginScreen(repo = repo, onLoginSuccess = {
                            loggedEmail = AuthManager.getEmail(this@MainActivity)
                            nav.navigate("home") { popUpTo("login") { inclusive = true } }
                        })
                    }
                    composable("home") {
                        HomeScreen(
                            repo = repo, userEmail = loggedEmail ?: "",
                            onAddClick = { nav.navigate("form") },
                            onEditClick = { f -> freteEditTarget.value = f.id; nav.navigate("form?edit=1") },
                            onPlacasClick = { nav.navigate("placas") },
                            onFretesClick = { nav.navigate("fretes") },
                            onRelatoriosClick = { nav.navigate("relatorios") },
                            onBackupClick = { nav.navigate("backup") },
                            onLogout = {
                                AuthManager.logout(this@MainActivity)
                                loggedEmail = null
                                nav.navigate("login") { popUpTo(0) { inclusive = true } }
                            }
                        )
                    }
                    composable("placas") { PlacasScreen(repo) { nav.popBackStack() } }
                    composable("fretes") { nav.popBackStack() }
                    composable("relatorios") { RelatoriosScreen(repo) { nav.popBackStack() } }
                    composable("backup") { BackupScreen(repo) { nav.popBackStack() } }
                    composable("saldo") { SaldoReceberScreen(repo) { nav.popBackStack() } }
                    composable("form?edit={edit}", arguments = listOf(navArgument("edit") { 
                        type = NavType.StringType; defaultValue = "0" 
                    })) { backStackEntry ->
                        val isEdit = backStackEntry.arguments?.getString("edit") == "1"
                        val targetId = freteEditTarget.value
                        var frete by remember { mutableStateOf<com.gerfrota.fretes.data.FreteEntity?>(null) }
                        var loaded by remember { mutableStateOf(!isEdit) }
                        
                        LaunchedEffect(targetId, isEdit) {
                            if (isEdit && targetId != null) {
                                frete = repo.getById(targetId)
                                loaded = true
                            }
                        }
                        
                        if (!loaded) {
                            Box(modifier = androidx.compose.ui.Modifier.fillMaxSize(), contentAlignment = androidx.compose.ui.Alignment.Center) {
                                androidx.compose.material3.CircularProgressIndicator()
                            }
                        } else {
                            FreteFormScreen(repo = repo, freteParaEditar = if (isEdit) frete else null, onBack = { freteEditTarget.value = null; nav.popBackStack() })
                        }
                    }
                }
            }
        }
    }
}
'''

# 25-30. Recursos
A["app/src/main/res/drawable/ic_truck_logo.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#1976D2" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#0D47A1" android:pathData="M0,54 L108,54 L108,108 L0,108z"/>
    <path android:fillColor="#FFFFFF" android:pathData="M20,60 L20,40 L60,40 L60,50 L75,50 L85,60 L85,72 L80,72 A8,8 0 0,1 64,72 L44,72 A8,8 0 0,1 28,72 L20,72 Z"/>
    <path android:fillColor="#FFC107" android:pathData="M36,72 m-6,0 a6,6 0 1,0 12,0 a6,6 0 1,0 -12,0"/>
    <path android:fillColor="#FFC107" android:pathData="M72,72 m-6,0 a6,6 0 1,0 12,0 a6,6 0 1,0 -12,0"/>
    <path android:fillColor="#81D4FA" android:pathData="M64,52 L73,52 L80,60 L64,60 Z"/>
    <path android:fillColor="#FFC107" android:pathData="M25,45 L35,45 L35,55 L25,55 Z"/>
    <path android:fillColor="#FFA000" android:pathData="M38,45 L48,45 L48,55 L38,55 Z"/>
    <path android:fillColor="#FFC107" android:pathData="M51,45 L58,45 L58,55 L51,55 Z"/>
</vector>
'''
A["app/src/main/res/values/colors.xml"] = r'''<?xml version="1.0" encoding="utf-8"?><resources>
    <color name="ic_launcher_background">#1976D2</color>
    <color name="primary">#1976D2</color>
    <color name="primary_dark">#0D47A1</color>
    <color name="accent">#FFC107</color>
    <color name="success">#4CAF50</color>
</resources>
'''
A["app/src/main/res/values/strings.xml"] = r'''<resources><string name="app_name">GerFrota Fretes</string></resources>
'''
A["app/src/main/res/values/themes.xml"] = r'''<resources><style name="Theme.GerFrotaFretes" parent="android:Theme.Material.Light.NoActionBar"/></resources>
'''
A["app/src/main/res/xml/file_paths.xml"] = r'''<?xml version="1.0" encoding="utf-8"?><paths>
    <external-path name="external_files" path="."/>
    <external-files-path name="external_files2" path="."/>
    <cache-path name="cache" path="."/>
    <files-path name="files" path="."/>
</paths>
'''
A["app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_truck_logo"/>
</adaptive-icon>
'''
A["app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_truck_logo"/>
</adaptive-icon>
'''

# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def criar_projeto():
    print("=" * 60)
    print("  GERADOR DO PROJETO GerFrota Fretes v2.1")
    print("  Versao Final Completa (Formas de Pagto + Relatorios)")
    print("=" * 60)
    print()
    if os.path.exists(PROJETO):
        resposta = input(f"A pasta '{PROJETO}' ja existe. Deseja sobrescrever? (s/N): ")
        if resposta.lower() != 's':
            print("Operacao cancelada.")
            return
        import shutil
        shutil.rmtree(PROJETO)
    total = len(A)
    criado = 0
    for caminho, conteudo in A.items():
        caminho_completo = os.path.join(PROJETO, caminho)
        diretorio = os.path.dirname(caminho_completo)
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(conteudo.lstrip('\n'))
        criado += 1
        print(f"  [{criado}/{total}] {caminho}")
    print()
    print("=" * 60)
    print(f"  PROJETO CRIADO COM SUCESSO!")
    print("=" * 60)
    print()
    print(f"  Pasta: {os.path.abspath(PROJETO)}")
    print(f"  Arquivos: {criado}")
    print()
    print("  PROXIMOS PASSOS:")
    print("  1. Commit e push no GitHub")
    print("  2. GitHub Actions compilara automaticamente")
    print("  3. Baixe o APK em Actions > Artifacts")
    print("=" * 60)

if __name__ == "__main__":
    try:
        criar_projeto()
    except KeyboardInterrupt:
        print("\n\nOperacao cancelada.")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro: {e}")
        sys.exit(1)
