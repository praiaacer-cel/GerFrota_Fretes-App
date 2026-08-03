#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERADOR DO PROJETO GerFrota Fretes - VERSÃO COMPLETA COM TELA DE PLACAS
"""

import os
import sys

PROJETO = "GerFrotaFretesApp"
ARQUIVOS = {}

# === settings.gradle.kts ===
ARQUIVOS["settings.gradle.kts"] = r'''pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "GerFrotaFretes"
include(":app")
'''

# === build.gradle.kts (raiz) ===
ARQUIVOS["build.gradle.kts"] = r'''plugins {
    id("com.android.application") version "8.2.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.20" apply false
    id("com.google.devtools.ksp") version "1.9.20-1.0.14" apply false
}
'''

# === gradle.properties ===
ARQUIVOS["gradle.properties"] = r'''org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
'''

# === app/build.gradle.kts ===
ARQUIVOS["app/build.gradle.kts"] = r'''plugins {
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
        versionCode = 1
        versionName = "1.0"
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
    implementation("com.google.api-client:google-api-client-android:2.2.0") {
        exclude(group = "org.apache.httpcomponents")
    }
    implementation("com.google.apis:google-api-services-drive:v3-rev20230816-2.0.0") {
        exclude(group = "org.apache.httpcomponents")
    }
    implementation("com.google.auth:google-auth-library-oauth2-http:1.22.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")
}
'''

# === AndroidManifest.xml ===
ARQUIVOS["app/src/main/AndroidManifest.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.RECORD_AUDIO"/>
    <uses-permission android:name="android.permission.GET_ACCOUNTS" android:maxSdkVersion="22"/>
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28"/>
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.GerFrotaFretes">
        <activity android:name=".MainActivity" android:exported="true" android:theme="@style/Theme.GerFrotaFretes">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/file_paths"/>
        </provider>
    </application>
</manifest>
'''

# === data/FreteEntity.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/data/FreteEntity.kt"] = r'''package com.gerfrota.fretes.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "fretes")
data class FreteEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val data: String, val placa: String, val valorFrete: Double,
    val adiantamento: Double, val formaPgtoAdiant: String,
    val saldoFrete: Double, val formaPgtoSaldo: String,
    val recebido: Boolean, val transportadora: String,
    val origem: String, val destino: String, val syncStatus: Int = 0
)

object FormasPagamento {
    val opcoes = listOf("Dinheiro", "PIX", "Transferência Bancária",
        "Cartão Débito", "Cartão Crédito", "Cheque",
        "Boleto", "Vale-Frete", "Depósito", "Outros")
}

object Placas {
    val lista = listOf("MLH 6C45", "QEW 8G04", "IWU 3D11", "ITL 4F00", "IXL 6H19")
}

data class PlacaResumo(
    val placa: String, val totalFretes: Int,
    val totalValor: Double, val totalAdiantamento: Double,
    val totalSaldo: Double, val totalRecebido: Double
)
'''

# === data/FreteDao.kt (COM NOVAS QUERIES) ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/data/FreteDao.kt"] = r'''package com.gerfrota.fretes.data

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
    @Query("SELECT transportadora, SUM(saldoFrete) as total FROM fretes WHERE recebido = 0 GROUP BY transportadora ORDER BY total DESC")
    fun saldoPorTransportadora(): Flow<List<SaldoTransportadora>>
    @Query("SELECT SUM(saldoFrete) FROM fretes WHERE recebido = 0")
    fun saldoTotalAReceber(): Flow<Double?>
    
    @Query("""
        SELECT placa, COUNT(*) as totalFretes,
               SUM(valorFrete) as totalValor,
               SUM(adiantamento) as totalAdiantamento,
               SUM(saldoFrete) as totalSaldo,
               SUM(CASE WHEN recebido = 1 THEN saldoFrete ELSE 0 END) as totalRecebido
        FROM fretes GROUP BY placa ORDER BY totalSaldo DESC
    """)
    fun resumoPorPlaca(): Flow<List<PlacaResumo>>
    
    @Query("SELECT * FROM fretes WHERE placa = :placa ORDER BY id DESC")
    fun getFretesPorPlaca(placa: String): Flow<List<FreteEntity>>
}

data class SaldoTransportadora(val transportadora: String, val total: Double)
'''

# === data/AppDatabase.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/data/AppDatabase.kt"] = r'''package com.gerfrota.fretes.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [FreteEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun freteDao(): FreteDao
    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null
        fun get(context: Context): AppDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext, AppDatabase::class.java, "gerfrota.db"
                ).build().also { INSTANCE = it }
            }
    }
}
'''

# === data/Repository.kt (COM NOVAS FUNÇÕES) ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/data/Repository.kt"] = r'''package com.gerfrota.fretes.data

import kotlinx.coroutines.flow.Flow

class Repository(private val dao: FreteDao) {
    val fretes: Flow<List<FreteEntity>> = dao.getAll()
    val saldoPorTransportadora: Flow<List<SaldoTransportadora>> = dao.saldoPorTransportadora()
    val saldoTotal: Flow<Double?> = dao.saldoTotalAReceber()
    val resumoPorPlaca: Flow<List<PlacaResumo>> = dao.resumoPorPlaca()

    suspend fun insert(f: FreteEntity) = dao.insert(f)
    suspend fun insertAll(fretes: List<FreteEntity>) = dao.insertAll(fretes)
    suspend fun update(f: FreteEntity) = dao.update(f)
    suspend fun delete(f: FreteEntity) = dao.delete(f)
    suspend fun deleteAll() = dao.deleteAll()
    suspend fun count(): Int = dao.count()
    suspend fun getById(id: Long): FreteEntity? = dao.getById(id)
    fun fretesPorPlaca(placa: String): Flow<List<FreteEntity>> = dao.getFretesPorPlaca(placa)
}
'''

# === data/AuthManager.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/data/AuthManager.kt"] = r'''package com.gerfrota.fretes.data

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
        prefs(ctx).edit().apply {
            putString("email", email.trim().lowercase())
            putString("pass_hash", hash(password))
            putBoolean("logged", true)
            apply()
        }
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

# === data/PdfExporter.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/data/PdfExporter.kt"] = r'''package com.gerfrota.fretes.data

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
    suspend fun exportar(context: Context, fretes: List<FreteEntity>, titulo: String = "Relatório de Fretes"): PdfResult = withContext(Dispatchers.IO) {
        runCatching {
            val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
            val df = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale("pt", "BR"))
            val pdf = PdfDocument()
            val pageW = 595; val pageH = 842; val margin = 30f
            val pTitle = Paint().apply { color = Color.parseColor("#0D47A1"); textSize = 20f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pSub = Paint().apply { color = Color.parseColor("#1976D2"); textSize = 11f; isAntiAlias = true }
            val pHead = Paint().apply { color = Color.WHITE; textSize = 9f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pCell = Paint().apply { color = Color.BLACK; textSize = 8.5f; isAntiAlias = true }
            val pBold = Paint().apply { color = Color.BLACK; textSize = 8.5f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val pBgH = Paint().apply { color = Color.parseColor("#1976D2") }
            val pBgA = Paint().apply { color = Color.parseColor("#F5F5F5") }
            val pBord = Paint().apply { color = Color.parseColor("#BDBDBD"); style = Paint.Style.STROKE; strokeWidth = 0.5f }
            val pTot = Paint().apply { color = Color.parseColor("#0D47A1"); textSize = 12f; isAntiAlias = true; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD) }
            val colX = floatArrayOf(margin, margin + 60, margin + 120, margin + 210, margin + 340, margin + 390, margin + 440, margin + 485)
            val headers = arrayOf("Data", "Placa", "Transportadora", "Rota", "Valor", "Adiant.", "Saldo", "Pgto Saldo")
            val rowH = 18f; val headerY = 90f; val rowsPerPage = 35
            val totalPag = kotlin.math.max(1, kotlin.math.ceil(fretes.size.toDouble() / rowsPerPage).toInt())
            var tV = 0.0; var tA = 0.0; var tS = 0.0
            for (pg in 0 until totalPag) {
                val page = pdf.startPage(PdfDocument.PageInfo.Builder(pageW, pageH, pg).create())
                val c = page.canvas
                c.drawText(titulo, margin, 40f, pTitle)
                c.drawText("Gerado em ${df.format(Date())} • Página ${pg + 1} de $totalPag", margin, 58f, pSub)
                c.drawLine(margin, 68f, pageW - margin, 68f, pBord)
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
                    c.drawText("${f.origem.ifBlank{"-"}} → ${f.destino.ifBlank{"-"}}".take(28), colX[3], y, pCell)
                    c.drawText(nf.format(f.valorFrete), colX[4], y, pCell)
                    c.drawText(nf.format(f.adiantamento), colX[5], y, pCell)
                    c.drawText(nf.format(f.saldoFrete), colX[6], y, if (f.saldoFrete > 0) pBold else pCell)
                    c.drawText(f.formaPgtoSaldo.take(14), colX[7], y, pCell)
                    tV += f.valorFrete; tA += f.adiantamento; tS += f.saldoFrete
                    y += rowH
                }
                c.drawRect(margin, headerY - 12f, pageW - margin, y, pBord)
                if (pg == totalPag - 1) {
                    val ty = y + 25f
                    c.drawText("TOTAIS:", margin, ty, pTot)
                    c.drawText("Valor: ${nf.format(tV)}", margin, ty + 18f, pBold)
                    c.drawText("Adiantamentos: ${nf.format(tA)}", margin + 170f, ty + 18f, pBold)
                    c.drawText("Saldo a Receber: ${nf.format(tS)}", margin + 360f, ty + 18f, pTot)
                    c.drawText("Total de registros: ${fretes.size}", margin, ty + 38f, pSub)
                }
                pdf.finishPage(page)
            }
            val fileName = "GerFrota_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale("pt","BR")).format(Date())}.pdf"
            val folder = File(context.filesDir, "pdfs").apply { if (!exists()) mkdirs() }
            val file = File(folder, fileName)
            FileOutputStream(file).use { out -> pdf.writeTo(out) }
            pdf.close()
            val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
            PdfResult(true, "PDF gerado!", uri)
        }.getOrElse { PdfResult(false, "Erro: ${it.message}") }
    }
}
'''

# === ui/LoginScreen.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/ui/LoginScreen.kt"] = r'''package com.gerfrota.fretes.ui

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
import com.gerfrota.fretes.drive.DriveBackupManager
import com.gerfrota.fretes.drive.RestoreResult
import kotlinx.coroutines.launch

@Composable
fun LoginScreen(repo: Repository, onLoginSuccess: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val backupManager = remember { DriveBackupManager(context) }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var isRegisterMode by remember { mutableStateOf(!AuthManager.isRegistered(context)) }
    var loading by remember { mutableStateOf(false) }
    var restoring by remember { mutableStateOf(false) }
    var showRestoreDialog by remember { mutableStateOf(false) }
    var fretesRestaurados by remember { mutableStateOf<List<com.gerfrota.fretes.data.FreteEntity>?>(null) }

    Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.primary) {
        Column(modifier = Modifier.fillMaxSize().padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center) {
            Image(painter = painterResource(R.drawable.ic_truck_logo), contentDescription = null, modifier = Modifier.size(140.dp))
            Spacer(Modifier.height(20.dp))
            Text("GerFrota Fretes", fontSize = 30.sp, fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimary, textAlign = TextAlign.Center)
            Text(if (isRegisterMode) "Crie sua conta" else "Entre com sua conta",
                fontSize = 15.sp, color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.85f))
            Spacer(Modifier.height(32.dp))
            Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
                Column(Modifier.padding(20.dp)) {
                    OutlinedTextField(value = email, onValueChange = { email = it },
                        label = { Text("E-mail") }, leadingIcon = { Icon(Icons.Default.Email, null) },
                        modifier = Modifier.fillMaxWidth(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email), singleLine = true)
                    Spacer(Modifier.height(12.dp))
                    OutlinedTextField(value = password, onValueChange = { password = it },
                        label = { Text("Senha") }, leadingIcon = { Icon(Icons.Default.Lock, null) },
                        modifier = Modifier.fillMaxWidth(),
                        visualTransformation = PasswordVisualTransformation(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password), singleLine = true)
                    if (isRegisterMode) {
                        Spacer(Modifier.height(12.dp))
                        OutlinedTextField(value = confirmPassword, onValueChange = { confirmPassword = it },
                            label = { Text("Confirmar senha") }, leadingIcon = { Icon(Icons.Default.Lock, null) },
                            modifier = Modifier.fillMaxWidth(),
                            visualTransformation = PasswordVisualTransformation(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password), singleLine = true)
                    }
                    Spacer(Modifier.height(20.dp))
                    Button(onClick = {
                        if (loading) return@Button
                        loading = true
                        if (isRegisterMode) {
                            if (password != confirmPassword) {
                                Toast.makeText(context, "As senhas não conferem", Toast.LENGTH_SHORT).show()
                                loading = false; return@Button
                            }
                            if (AuthManager.registrar(context, email, password)) {
                                Toast.makeText(context, "Conta criada!", Toast.LENGTH_SHORT).show()
                                onLoginSuccess()
                            } else {
                                Toast.makeText(context, "Preencha e-mail e senha (mín. 4)", Toast.LENGTH_SHORT).show()
                            }
                        } else {
                            when (AuthManager.login(context, email, password)) {
                                LoginResult.SUCCESS -> onLoginSuccess()
                                LoginResult.WRONG_EMAIL -> Toast.makeText(context, "E-mail não cadastrado", Toast.LENGTH_SHORT).show()
                                LoginResult.WRONG_PASSWORD -> Toast.makeText(context, "Senha incorreta", Toast.LENGTH_SHORT).show()
                                LoginResult.NOT_REGISTERED -> {
                                    isRegisterMode = true
                                    Toast.makeText(context, "Crie uma conta", Toast.LENGTH_SHORT).show()
                                }
                            }
                        }
                        loading = false
                    }, modifier = Modifier.fillMaxWidth().height(52.dp),
                        shape = RoundedCornerShape(12.dp), enabled = !loading) {
                        if (loading) CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                        else Text(if (isRegisterMode) "📝 CRIAR CONTA" else "🔐 ENTRAR", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    }
                    if (AuthManager.isRegistered(context)) {
                        Spacer(Modifier.height(8.dp))
                        TextButton(onClick = { isRegisterMode = !isRegisterMode }, modifier = Modifier.fillMaxWidth()) {
                            Text(if (isRegisterMode) "Já tenho conta — Entrar" else "Não tenho conta — Criar agora", fontSize = 13.sp)
                        }
                    }
                    Spacer(Modifier.height(12.dp))
                    HorizontalDivider(color = Color.Gray.copy(alpha = 0.3f))
                    Spacer(Modifier.height(12.dp))
                    OutlinedButton(onClick = {
                        if (restoring) return@OutlinedButton
                        restoring = true
                        scope.launch {
                            when (val result = backupManager.restore()) {
                                is RestoreResult.Success -> {
                                    restoring = false
                                    if (result.fretes.isEmpty()) Toast.makeText(context, "Backup vazio", Toast.LENGTH_SHORT).show()
                                    else { fretesRestaurados = result.fretes; showRestoreDialog = true }
                                }
                                is RestoreResult.Error -> {
                                    restoring = false
                                    Toast.makeText(context, result.message, Toast.LENGTH_LONG).show()
                                }
                            }
                        }
                    }, modifier = Modifier.fillMaxWidth(), enabled = !restoring) {
                        if (restoring) {
                            CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                            Spacer(Modifier.width(8.dp)); Text("Buscando backup...")
                        } else {
                            Icon(Icons.Default.CloudDownload, null, tint = MaterialTheme.colorScheme.primary)
                            Spacer(Modifier.width(8.dp)); Text("Restaurar backup do Drive", fontSize = 13.sp)
                        }
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
            Text("Seus dados ficam salvos no dispositivo\ne com backup no Google Drive",
                fontSize = 12.sp, color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f),
                textAlign = TextAlign.Center)
        }
    }
    if (showRestoreDialog && fretesRestaurados != null) {
        val fretes = fretesRestaurados!!
        AlertDialog(onDismissRequest = { showRestoreDialog = false; fretesRestaurados = null },
            icon = { Icon(Icons.Default.CloudDownload, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(40.dp)) },
            title = { Text("Backup encontrado!") },
            text = {
                Column {
                    Text("${fretes.size} fretes encontrados no backup.")
                    Spacer(Modifier.height(8.dp))
                    Text("• Substituir: apaga fretes atuais e importa backup", fontSize = 12.sp)
                    Text("• Mesclar: mantém atuais e adiciona do backup", fontSize = 12.sp)
                }
            },
            confirmButton = {
                Column {
                    TextButton(onClick = {
                        scope.launch {
                            repo.deleteAll(); repo.insertAll(fretes)
                            showRestoreDialog = false; fretesRestaurados = null
                            Toast.makeText(context, "✅ ${fretes.size} fretes restaurados!", Toast.LENGTH_LONG).show()
                            onLoginSuccess()
                        }
                    }) { Text("🔄 SUBSTITUIR TUDO", color = Color.Red, fontWeight = FontWeight.Bold) }
                    TextButton(onClick = {
                        scope.launch {
                            repo.insertAll(fretes)
                            showRestoreDialog = false; fretesRestaurados = null
                            Toast.makeText(context, "✅ ${fretes.size} fretes adicionados!", Toast.LENGTH_LONG).show()
                            onLoginSuccess()
                        }
                    }) { Text("➕ MESCLAR COM ATUAIS", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold) }
                }
            },
            dismissButton = { TextButton(onClick = { showRestoreDialog = false; fretesRestaurados = null }) { Text("Cancelar") } })
    }
}
'''

# === ui/HomeScreen.kt (COM NOVO CARD DE PLACAS) ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/ui/HomeScreen.kt"] = r'''package com.gerfrota.fretes.ui

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
import com.gerfrota.fretes.drive.DriveBackupManager
import com.gerfrota.fretes.drive.RestoreResult
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    repo: Repository, userEmail: String, driveAccountEmail: String?,
    onAddClick: () -> Unit, onEditClick: (FreteEntity) -> Unit,
    onSaldoClick: () -> Unit, onPlacasClick: () -> Unit, onLogout: () -> Unit
) {
    val fretes by repo.fretes.collectAsState(initial = emptyList())
    val saldoTotal by repo.saldoTotal.collectAsState(initial = 0.0)
    val scope = rememberCoroutineScope()
    val nf = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
    val context = LocalContext.current
    var exportando by remember { mutableStateOf(false) }
    var pdfUri by remember { mutableStateOf<android.net.Uri?>(null) }
    var showShareDialog by remember { mutableStateOf(false) }
    var menuOpen by remember { mutableStateOf(false) }
    var showRestoreDialog by remember { mutableStateOf(false) }
    var fretesRestaurados by remember { mutableStateOf<List<FreteEntity>?>(null) }
    val backupManager = remember { DriveBackupManager(context) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("GerFrota Fretes", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        if (driveAccountEmail != null) {
                            Text("🔄 Drive: $driveAccountEmail", fontSize = 10.sp, color = Color.White.copy(alpha = 0.8f))
                        } else {
                            Text("⚠️ Sem conta Google no dispositivo", fontSize = 10.sp, color = Color.Yellow)
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { menuOpen = true }) {
                        Icon(Icons.Default.MoreVert, "Mais", tint = Color.White)
                    }
                    DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                        DropdownMenuItem(
                            text = { Text("🔄 Restaurar backup do Drive") },
                            onClick = {
                                menuOpen = false
                                scope.launch {
                                    when (val r = backupManager.restore()) {
                                        is RestoreResult.Success -> {
                                            if (r.fretes.isEmpty()) Toast.makeText(context, "Backup vazio", Toast.LENGTH_SHORT).show()
                                            else { fretesRestaurados = r.fretes; showRestoreDialog = true }
                                        }
                                        is RestoreResult.Error -> Toast.makeText(context, r.message, Toast.LENGTH_LONG).show()
                                    }
                                }
                            },
                            leadingIcon = { Icon(Icons.Default.CloudDownload, null) }
                        )
                    }
                    IconButton(onClick = {
                        if (!exportando) {
                            if (fretes.isEmpty()) { Toast.makeText(context, "Nenhum frete", Toast.LENGTH_SHORT).show(); return@IconButton }
                            exportando = true
                            scope.launch {
                                val r = PdfExporter.exportar(context, fretes, "Relatório de Fretes")
                                exportando = false
                                if (r.success && r.uri != null) { pdfUri = r.uri; showShareDialog = true }
                                else Toast.makeText(context, r.message, Toast.LENGTH_LONG).show()
                            }
                        }
                    }) {
                        if (exportando) CircularProgressIndicator(modifier = Modifier.size(24.dp), color = Color.White)
                        else Icon(Icons.Default.PictureAsPdf, "PDF", tint = Color.White)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(userEmail, fontSize = 11.sp, color = Color.White, modifier = Modifier.padding(end = 8.dp, top = 4.dp))
                        IconButton(onClick = onLogout) { Icon(Icons.Default.Logout, "Sair", tint = Color.White) }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = Color.White,
                    actionIconContentColor = Color.White
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = onAddClick, containerColor = MaterialTheme.colorScheme.secondary) {
                Icon(Icons.Default.Add, "Novo Frete", tint = Color.White)
            }
        }
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            // 2 CARDS LADO A LADO
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Card(modifier = Modifier.weight(1f).clickable { onSaldoClick() },
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                    Column(Modifier.padding(12.dp)) {
                        Text("💰 SALDO", fontSize = 11.sp, fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f))
                        Text(nf.format(saldoTotal ?: 0.0), fontSize = 16.sp, fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer)
                        Text("Por transportadora →", fontSize = 10.sp,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f))
                    }
                }
                Card(modifier = Modifier.weight(1f).clickable { onPlacasClick() },
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer)) {
                    Column(Modifier.padding(12.dp)) {
                        Text("🚛 PLACAS", fontSize = 11.sp, fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onTertiaryContainer.copy(alpha = 0.7f))
                        Text("5 placas", fontSize = 16.sp, fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onTertiaryContainer)
                        Text("Ver fretes por placa →", fontSize = 10.sp,
                            color = MaterialTheme.colorScheme.onTertiaryContainer.copy(alpha = 0.7f))
                    }
                }
            }
            Text("  Últimos fretes", fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
            if (fretes.isEmpty()) {
                Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) {
                    Text("Nenhum frete cadastrado.\nToque no + para adicionar.",
                        textAlign = Alignment.Center, color = Color.Gray)
                }
            } else {
                LazyColumn {
                    items(fretes) { f ->
                        FreteItem(f, nf, onEdit = { onEditClick(f) }, onDelete = { scope.launch { repo.delete(f) } })
                    }
                }
            }
        }
    }
    if (showShareDialog && pdfUri != null) {
        AlertDialog(onDismissRequest = { showShareDialog = false },
            icon = { Icon(Icons.Default.CheckCircle, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(40.dp)) },
            title = { Text("PDF Gerado!") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Escolha como compartilhar:")
                    OutlinedButton(onClick = { compartilharWhatsApp(context, pdfUri!!); showShareDialog = false }, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.Chat, null, tint = Color(0xFF25D366))
                        Spacer(Modifier.width(8.dp)); Text("Enviar por WhatsApp")
                    }
                    OutlinedButton(onClick = { compartilharEmail(context, pdfUri!!); showShareDialog = false }, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.Email, null, tint = Color(0xFFD93025))
                        Spacer(Modifier.width(8.dp)); Text("Enviar por E-mail")
                    }
                    Button(onClick = { compartilharGenerico(context, pdfUri!!); showShareDialog = false },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)) {
                        Icon(Icons.Default.Share, null); Spacer(Modifier.width(8.dp)); Text("Compartilhar (outros apps)")
                    }
                }
            },
            confirmButton = { TextButton(onClick = { showShareDialog = false }) { Text("Fechar") } })
    }
    if (showRestoreDialog && fretesRestaurados != null) {
        val fretes = fretesRestaurados!!
        AlertDialog(onDismissRequest = { showRestoreDialog = false; fretesRestaurados = null },
            icon = { Icon(Icons.Default.CloudDownload, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(40.dp)) },
            title = { Text("Backup encontrado!") },
            text = {
                Column {
                    Text("${fretes.size} fretes encontrados no backup.")
                    Spacer(Modifier.height(8.dp))
                    Text("• Substituir: apaga fretes atuais e importa backup", fontSize = 12.sp)
                    Text("• Mesclar: mantém atuais e adiciona do backup", fontSize = 12.sp)
                }
            },
            confirmButton = {
                Column {
                    TextButton(onClick = {
                        scope.launch {
                            repo.deleteAll(); repo.insertAll(fretes)
                            showRestoreDialog = false; fretesRestaurados = null
                            Toast.makeText(context, "✅ ${fretes.size} fretes restaurados!", Toast.LENGTH_LONG).show()
                        }
                    }) { Text("🔄 SUBSTITUIR TUDO", color = Color.Red, fontWeight = FontWeight.Bold) }
                    TextButton(onClick = {
                        scope.launch {
                            repo.insertAll(fretes)
                            showRestoreDialog = false; fretesRestaurados = null
                            Toast.makeText(context, "✅ ${fretes.size} fretes mesclados!", Toast.LENGTH_LONG).show()
                        }
                    }) { Text("➕ MESCLAR", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold) }
                }
            },
            dismissButton = { TextButton(onClick = { showRestoreDialog = false; fretesRestaurados = null }) { Text("Cancelar") } })
    }
}

private fun compartilharWhatsApp(ctx: android.content.Context, uri: android.net.Uri) {
    try {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/pdf"; putExtra(Intent.EXTRA_STREAM, uri)
            setPackage("com.whatsapp"); addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        ctx.startActivity(intent)
    } catch (e: Exception) {
        Toast.makeText(ctx, "WhatsApp não instalado", Toast.LENGTH_SHORT).show()
        compartilharGenerico(ctx, uri)
    }
}

private fun compartilharEmail(ctx: android.content.Context, uri: android.net.Uri) {
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "application/pdf"; putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_SUBJECT, "Relatório de Fretes")
        putExtra(Intent.EXTRA_TEXT, "Segue relatório gerado pelo app GerFrota Fretes.")
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    ctx.startActivity(Intent.createChooser(intent, "Enviar por e-mail"))
}

private fun compartilharGenerico(ctx: android.content.Context, uri: android.net.Uri) {
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "application/pdf"; putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_SUBJECT, "Relatório de Fretes")
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    ctx.startActivity(Intent.createChooser(intent, "Compartilhar PDF via..."))
}

@Composable
fun FreteItem(f: FreteEntity, nf: NumberFormat, onEdit: () -> Unit, onDelete: () -> Unit) {
    var showDelete by remember { mutableStateOf(false) }
    Card(modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
        elevation = CardDefaults.cardElevation(2.dp)) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(f.transportadora.ifBlank { "Sem transportadora" },
                    fontWeight = FontWeight.Bold, fontSize = 16.sp, modifier = Modifier.weight(1f))
                Text(nf.format(f.saldoFrete), fontWeight = FontWeight.Bold,
                    color = if (f.recebido) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
            }
            Text("${f.origem} → ${f.destino}", fontSize = 13.sp, color = Color.Gray)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("${f.data} • ${f.placa}", fontSize = 12.sp, color = Color.Gray)
                Row {
                    TextButton(onClick = onEdit) {
                        Icon(Icons.Default.Edit, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp)); Text("Editar", color = MaterialTheme.colorScheme.primary, fontSize = 12.sp)
                    }
                    TextButton(onClick = { showDelete = true }) {
                        Icon(Icons.Default.Delete, null, tint = Color.Red, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp)); Text("Excluir", color = Color.Red, fontSize = 12.sp)
                    }
                }
            }
            if (f.recebido) Text("✅ RECEBIDO", fontSize = 11.sp, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
        }
    }
    if (showDelete) {
        AlertDialog(onDismissRequest = { showDelete = false },
            title = { Text("Excluir frete?") },
            text = { Text("${f.transportadora} - ${nf.format(f.valorFrete)}") },
            confirmButton = { TextButton(onClick = { showDelete = false; onDelete() }) { Text("Excluir", color = Color.Red) } },
            dismissButton = { TextButton(onClick = { showDelete = false }) { Text("Cancelar") } })
    }
}
'''

# === ui/PlacasScreen.kt (NOVO) ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/ui/PlacasScreen.kt"] = r'''package com.gerfrota.fretes.ui

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

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (placaSelecionada == null) "Fretes por Placa" else placaSelecionada!!) },
                navigationIcon = {
                    IconButton(onClick = {
                        if (placaSelecionada != null) placaSelecionada = null else onBack()
                    }) { Icon(Icons.Default.ArrowBack, "Voltar") }
                }
            )
        }
    ) { padding ->
        if (placaSelecionada == null) {
            Column(Modifier.padding(padding).fillMaxSize()) {
                val totalGeral = resumo.sumOf { it.totalSaldo }
                val fretesTotal = resumo.sumOf { it.totalFretes }
                Card(modifier = Modifier.fillMaxWidth().padding(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primary)) {
                    Column(Modifier.padding(20.dp).fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("TOTAL GERAL — TODAS AS PLACAS",
                            color = Color.White.copy(alpha = 0.85f), fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        Text(nf.format(totalGeral), color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                        Text("$fretesTotal fretes cadastrados", color = Color.White.copy(alpha = 0.8f), fontSize = 12.sp)
                    }
                }
                if (resumo.isEmpty()) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text("Nenhuma placa com fretes cadastrados", color = Color.Gray)
                    }
                } else {
                    LazyColumn(Modifier.padding(horizontal = 16.dp)) {
                        items(resumo) { r -> CardPlaca(r, nf) { placaSelecionada = r.placa } }
                    }
                }
            }
        } else {
            val fretes by repo.fretesPorPlaca(placaSelecionada!!).collectAsState(initial = emptyList())
            LazyColumn(Modifier.padding(padding).padding(horizontal = 16.dp)) {
                items(fretes) { f -> FreteItemPlaca(f, nf) }
            }
        }
    }
}

@Composable
fun CardPlaca(resumo: PlacaResumo, nf: NumberFormat, onClick: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp).clickable { onClick() },
        elevation = CardDefaults.cardElevation(3.dp)) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.LocalShipping, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(32.dp))
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text(resumo.placa, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Text("${resumo.totalFretes} fretes", fontSize = 12.sp, color = Color.Gray)
                }
                Text(nf.format(resumo.totalSaldo), fontWeight = FontWeight.Bold, fontSize = 16.sp,
                    color = if (resumo.totalSaldo > 0) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary)
            }
            Spacer(Modifier.height(12.dp))
            HorizontalDivider(color = Color.Gray.copy(alpha = 0.2f))
            Spacer(Modifier.height(8.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                InfoItem("Valor Total", nf.format(resumo.totalValor))
                InfoItem("Adiantamentos", nf.format(resumo.totalAdiantamento))
            }
            Spacer(Modifier.height(4.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                InfoItem("Já Recebido", nf.format(resumo.totalRecebido), color = MaterialTheme.colorScheme.primary)
                InfoItem("Saldo Pendente", nf.format(resumo.totalSaldo), color = MaterialTheme.colorScheme.error)
            }
            Spacer(Modifier.height(8.dp))
            Text("Toque para ver os fretes →", fontSize = 11.sp,
                color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
fun InfoItem(label: String, value: String, color: Color = Color.Black) {
    Column {
        Text(label, fontSize = 10.sp, color = Color.Gray)
        Text(value, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = color)
    }
}

@Composable
fun FreteItemPlaca(f: FreteEntity, nf: NumberFormat) {
    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp), elevation = CardDefaults.cardElevation(2.dp)) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(f.transportadora.ifBlank { "Sem transportadora" }, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Text("${f.origem} → ${f.destino}", fontSize = 12.sp, color = Color.Gray)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(nf.format(f.saldoFrete), fontWeight = FontWeight.Bold, fontSize = 14.sp,
                        color = if (f.recebido) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
                    Text(f.data, fontSize = 11.sp, color = Color.Gray)
                }
            }
            Spacer(Modifier.height(4.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Valor: ${nf.format(f.valorFrete)}", fontSize = 11.sp, color = Color.Gray)
                Text("Adiant.: ${nf.format(f.adiantamento)}", fontSize = 11.sp, color = Color.Gray)
                if (f.recebido) Text("✅ RECEBIDO", fontSize = 11.sp, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
            }
        }
    }
}
'''

# === ui/FreteFormScreen.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/ui/FreteFormScreen.kt"] = r'''package com.gerfrota.fretes.ui

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

    Scaffold(topBar = {
        TopAppBar(title = { Text(if (isEdit) "Editar Frete" else "Novo Frete") },
            navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Voltar") } })
    }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp)) {
            VoiceField("Data", data, { data = it }, "data", "Fale a data", ::askVoice)
            VoiceField("Transportadora", transportadora, { transportadora = it }, "transportadora", "Fale o nome da transportadora", ::askVoice)
            VoiceField("Origem", origem, { origem = it }, "origem", "Fale a cidade de origem", ::askVoice)
            VoiceField("Destino", destino, { destino = it }, "destino", "Fale a cidade de destino", ::askVoice)
            Text("Placa", style = MaterialTheme.typography.labelMedium)
            var expanded by remember { mutableStateOf(false) }
            ExposedDropdownMenuBox(expanded, onExpandedChange = { expanded = it }) {
                OutlinedTextField(value = placa, onValueChange = { placa = it },
                    modifier = Modifier.menuAnchor().fillMaxWidth(),
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) })
                ExposedDropdownMenu(expanded, onDismissRequest = { expanded = false }) {
                    Placas.lista.forEach { p -> DropdownMenuItem(text = { Text(p) }, onClick = { placa = p; expanded = false }) }
                }
            }
            VoiceField("Valor do Frete (R$)", valorStr, { valorStr = it }, "valor", "Fale o valor", ::askVoice, KeyboardType.Decimal)
            VoiceField("Adiantamento (R$)", adiantStr, { adiantStr = it }, "adiant", "Fale o adiantamento", ::askVoice, KeyboardType.Decimal)
            Text("Forma Pagto Adiantamento", style = MaterialTheme.typography.labelMedium)
            var exp1 by remember { mutableStateOf(false) }
            ExposedDropdownMenuBox(exp1, onExpandedChange = { exp1 = it }) {
                OutlinedTextField(value = formaAdiant, onValueChange = {},
                    modifier = Modifier.menuAnchor().fillMaxWidth(), readOnly = true,
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(exp1) })
                ExposedDropdownMenu(exp1, onDismissRequest = { exp1 = false }) {
                    FormasPagamento.opcoes.forEach { o -> DropdownMenuItem(text = { Text(o) }, onClick = { formaAdiant = o; exp1 = false }) }
                }
            }
            Text("Forma Pagto Saldo", style = MaterialTheme.typography.labelMedium)
            var exp2 by remember { mutableStateOf(false) }
            ExposedDropdownMenuBox(exp2, onExpandedChange = { exp2 = it }) {
                OutlinedTextField(value = formaSaldo, onValueChange = {},
                    modifier = Modifier.menuAnchor().fillMaxWidth(), readOnly = true,
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(exp2) })
                ExposedDropdownMenu(exp2, onDismissRequest = { exp2 = false }) {
                    FormasPagamento.opcoes.forEach { o -> DropdownMenuItem(text = { Text(o) }, onClick = { formaSaldo = o; exp2 = false }) }
                }
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(checked = recebido, onCheckedChange = { recebido = it })
                Text("Já Recebido (SIM)")
            }
            Spacer(Modifier.height(16.dp))
            val valor = valorStr.toDoubleOrNull() ?: 0.0
            val adiant = adiantStr.toDoubleOrNull() ?: 0.0
            val saldo = valor - adiant
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                Row(Modifier.padding(16.dp).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Saldo do Frete:", fontWeight = FontWeight.Bold)
                    Text(NumberFormat.getCurrencyInstance(Locale("pt","BR")).format(saldo),
                        fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                }
            }
            Button(onClick = {
                if (salvando) return@Button
                salvando = true
                scope.launch {
                    val entity = FreteEntity(id = freteParaEditar?.id ?: 0,
                        data = data, placa = placa, valorFrete = valor,
                        adiantamento = adiant, formaPgtoAdiant = formaAdiant,
                        saldoFrete = saldo, formaPgtoSaldo = formaSaldo,
                        recebido = recebido, transportadora = transportadora,
                        origem = origem, destino = destino)
                    if (isEdit) repo.update(entity) else repo.insert(entity)
                    onBack()
                }
            }, modifier = Modifier.fillMaxWidth().height(56.dp), enabled = !salvando) {
                Text(if (isEdit) "💾 ATUALIZAR FRETE" else "💾 SALVAR FRETE", fontSize = 16.sp)
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
fun VoiceField(label: String, value: String, onChange: (String) -> Unit,
    voiceKey: String, voicePrompt: String, askVoice: (String, String) -> Unit,
    keyboard: KeyboardType = KeyboardType.Text) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        OutlinedTextField(value = value, onValueChange = onChange, label = { Text(label) },
            modifier = Modifier.weight(1f), keyboardOptions = KeyboardOptions(keyboardType = keyboard))
        Spacer(Modifier.width(8.dp))
        IconButton(onClick = { askVoice(voiceKey, voicePrompt) }, modifier = Modifier.size(48.dp)) {
            Icon(Icons.Default.Mic, "Falar", tint = MaterialTheme.colorScheme.primary)
        }
    }
}
'''

# === ui/SaldoReceberScreen.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/ui/SaldoReceberScreen.kt"] = r'''package com.gerfrota.fretes.ui

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
    Scaffold(topBar = {
        TopAppBar(title = { Text("Saldo a Receber") },
            navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Voltar") } })
    }) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            Card(modifier = Modifier.fillMaxWidth().padding(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primary)) {
                Column(Modifier.padding(20.dp).fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("TOTAL GERAL A RECEBER", color = Color.White.copy(alpha = 0.85f), fontWeight = FontWeight.Bold)
                    Text(nf.format(total ?: 0.0), color = Color.White, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                }
            }
            Text("  Por Transportadora", fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
            if (lista.isEmpty()) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Nenhum saldo pendente 🎉", color = Color.Gray)
                }
            } else {
                LazyColumn(Modifier.padding(horizontal = 16.dp)) {
                    items(lista) { item ->
                        Card(Modifier.fillMaxWidth().padding(vertical = 4.dp), elevation = CardDefaults.cardElevation(2.dp)) {
                            Row(Modifier.padding(16.dp).fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically) {
                                Text(item.transportadora.ifBlank { "(sem nome)" }, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                                Text(nf.format(item.total), fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.error, fontSize = 18.sp)
                            }
                        }
                    }
                }
            }
        }
    }
}
'''

# === ui/VoiceInputHelper.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/ui/VoiceInputHelper.kt"] = r'''package com.gerfrota.fretes.ui

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
        val cleaned = text.lowercase(Locale("pt","BR"))
            .replace("reais", "").replace("real", "")
            .replace("vírgula", ",").replace("virgula", ",")
            .replace("ponto", ".").trim()
        val regex = Regex("[0-9]+([.,][0-9]+)?")
        return regex.find(cleaned)?.value ?: cleaned
    }
}
'''

# === drive/DriveBackupManager.kt ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/drive/DriveBackupManager.kt"] = r'''package com.gerfrota.fretes.drive

import android.accounts.AccountManager
import android.content.Context
import com.google.api.client.googleapis.extensions.android.gms.auth.GoogleAccountCredential
import com.google.api.client.http.ByteArrayContent
import com.google.api.client.http.javanet.NetHttpTransport
import com.google.api.client.json.gson.GsonFactory
import com.google.api.services.drive.Drive
import com.google.api.services.drive.DriveScopes
import com.google.api.services.drive.model.File
import com.gerfrota.fretes.data.FreteEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader

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
    suspend fun backup(fretes: List<FreteEntity>): Pair<Boolean, String> = withContext(Dispatchers.IO) {
        runCatching {
            val accountEmail = getGoogleAccount() ?: return@withContext Pair(false, "Nenhuma conta Google no dispositivo.")
            val drive = buildDrive(accountEmail)
            val json = JSONArray().apply {
                fretes.forEach { f ->
                    put(JSONObject().apply {
                        put("id", f.id); put("data", f.data); put("placa", f.placa)
                        put("valorFrete", f.valorFrete); put("adiantamento", f.adiantamento)
                        put("formaPgtoAdiant", f.formaPgtoAdiant); put("saldoFrete", f.saldoFrete)
                        put("formaPgtoSaldo", f.formaPgtoSaldo); put("recebido", f.recebido)
                        put("transportadora", f.transportadora); put("origem", f.origem)
                        put("destino", f.destino)
                    })
                }
            }.toString()
            val query = "name='gerfrota_backup.json' and mimeType='application/json' and trashed=false"
            val existing = drive.files().list().setQ(query).setSpaces("drive").setFields("files(id, name)").execute()
            val metadata = File().apply { name = "gerfrota_backup.json"; mimeType = "application/json" }
            val content = ByteArrayContent.fromString("application/json", json)
            if (existing.files.isNullOrEmpty()) drive.files().create(metadata, content).setFields("id").execute()
            else drive.files().update(existing.files[0].id, metadata, content).execute()
            Pair(true, "Backup realizado em $accountEmail")
        }.getOrElse { Pair(false, "Erro no backup: ${it.message}") }
    }
    suspend fun restore(): RestoreResult = withContext(Dispatchers.IO) {
        runCatching {
            val accountEmail = getGoogleAccount() ?: return@withContext RestoreResult.Error("Nenhuma conta Google no dispositivo.")
            val drive = buildDrive(accountEmail)
            val query = "name='gerfrota_backup.json' and mimeType='application/json' and trashed=false"
            val files = drive.files().list().setQ(query).setSpaces("drive").setFields("files(id, name)").execute()
            if (files.files.isNullOrEmpty()) return@withContext RestoreResult.Error("Nenhum backup encontrado no Drive.")
            val fileId = files.files[0].id
            val inputStream = drive.files().get(fileId).executeAsInputStream()
            val reader = BufferedReader(InputStreamReader(inputStream, "UTF-8"))
            val jsonStr = reader.use { it.readText() }
            val jsonArray = JSONArray(jsonStr)
            val fretes = mutableListOf<FreteEntity>()
            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                fretes.add(FreteEntity(
                    id = 0, data = obj.optString("data", ""), placa = obj.optString("placa", ""),
                    valorFrete = obj.optDouble("valorFrete", 0.0), adiantamento = obj.optDouble("adiantamento", 0.0),
                    formaPgtoAdiant = obj.optString("formaPgtoAdiant", ""), saldoFrete = obj.optDouble("saldoFrete", 0.0),
                    formaPgtoSaldo = obj.optString("formaPgtoSaldo", ""), recebido = obj.optBoolean("recebido", false),
                    transportadora = obj.optString("transportadora", ""), origem = obj.optString("origem", ""),
                    destino = obj.optString("destino", "")
                ))
            }
            RestoreResult.Success(fretes, accountEmail)
        }.getOrElse { RestoreResult.Error("Erro ao restaurar: ${it.message}") }
    }
    fun getDriveAccountEmail(): String? = getGoogleAccount()
}

sealed class RestoreResult {
    data class Success(val fretes: List<FreteEntity>, val account: String) : RestoreResult()
    data class Error(val message: String) : RestoreResult()
}
'''

# === MainActivity.kt (COM ROTA DE PLACAS) ===
ARQUIVOS["app/src/main/java/com/gerfrota/fretes/MainActivity.kt"] = r'''package com.gerfrota.fretes

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
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
import com.gerfrota.fretes.drive.DriveBackupManager
import com.gerfrota.fretes.ui.*
import kotlinx.coroutines.flow.firstOrNull

class MainActivity : ComponentActivity() {
    private val repo by lazy { Repository(AppDatabase.get(this).freteDao()) }
    private val backup by lazy { DriveBackupManager(this) }
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
                            driveAccountEmail = backup.getDriveAccountEmail(),
                            onAddClick = { nav.navigate("form") },
                            onEditClick = { f -> freteEditTarget.value = f.id; nav.navigate("form?edit=1") },
                            onSaldoClick = { nav.navigate("saldo") },
                            onPlacasClick = { nav.navigate("placas") },
                            onLogout = {
                                AuthManager.logout(this@MainActivity)
                                loggedEmail = null
                                nav.navigate("login") { popUpTo(0) { inclusive = true } }
                            }
                        )
                        LaunchedEffect(loggedEmail) {
                            if (loggedEmail != null) {
                                val fretes = repo.fretes.firstOrNull() ?: emptyList()
                                backup.backup(fretes)
                            }
                        }
                    }
                    composable("placas") { PlacasScreen(repo) { nav.popBackStack() } }
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
                                frete = repo.fretes.firstOrNull()?.find { it.id == targetId }
                                loaded = true
                            }
                        }
                        if (!loaded) {
                            androidx.compose.foundation.layout.Box(
                                modifier = androidx.compose.ui.Modifier.fillMaxSize(),
                                contentAlignment = androidx.compose.ui.Alignment.Center
                            ) { androidx.compose.material3.CircularProgressIndicator() }
                        } else {
                            FreteFormScreen(repo = repo, freteParaEditar = if (isEdit) frete else null,
                                onBack = { freteEditTarget.value = null; nav.popBackStack() })
                        }
                    }
                }
            }
        }
    }
}
'''

# === RECURSOS ===
ARQUIVOS["app/src/main/res/drawable/ic_truck_logo.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
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

ARQUIVOS["app/src/main/res/values/colors.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#1976D2</color>
    <color name="primary">#1976D2</color>
    <color name="primary_dark">#0D47A1</color>
    <color name="accent">#FFC107</color>
    <color name="success">#4CAF50</color>
</resources>
'''

ARQUIVOS["app/src/main/res/values/strings.xml"] = r'''<resources>
    <string name="app_name">GerFrota Fretes</string>
</resources>
'''

ARQUIVOS["app/src/main/res/values/themes.xml"] = r'''<resources>
    <style name="Theme.GerFrotaFretes" parent="android:Theme.Material.Light.NoActionBar"/>
</resources>
'''

ARQUIVOS["app/src/main/res/xml/file_paths.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<paths>
    <external-path name="external_files" path="."/>
    <external-files-path name="external_files2" path="."/>
    <cache-path name="cache" path="."/>
    <files-path name="files" path="."/>
</paths>
'''

ARQUIVOS["app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_truck_logo"/>
</adaptive-icon>
'''

ARQUIVOS["app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_truck_logo"/>
</adaptive-icon>
'''

# === README.md ===
ARQUIVOS["README.md"] = r'''# 🚛 GerFrota Fretes

App Android para controle de fretes com backup no Google Drive.

## Funcionalidades
- Login local (e-mail + senha)
- Backup/restauração no Google Drive
- Entrada por voz (microfone)
- Edição de fretes
- Exportação PDF + Compartilhamento (WhatsApp/E-mail)
- Saldo a receber por transportadora
- **NOVO: Fretes agrupados por placa** (5 placas)
- 10 formas de pagamento

## Placas: MLH 6C45, QEW 8G04, IWU 3D11, ITL 4F00, IXL 6H19

## Como compilar
1. Abra no Android Studio
2. Configure Google Drive API (veja console.cloud.google.com)
3. Build → Build APK
'''

# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def criar_projeto():
    print("=" * 60)
    print("  GERADOR DO PROJETO GerFrota Fretes")
    print("  Versão com Tela de Placas")
    print("=" * 60)
    print()
    if os.path.exists(PROJETO):
        resposta = input(f"⚠️  A pasta '{PROJETO}' já existe. Deseja sobrescrever? (s/N): ")
        if resposta.lower() != 's':
            print("❌ Operação cancelada.")
            return
        import shutil
        shutil.rmtree(PROJETO)
    total = len(ARQUIVOS)
    criado = 0
    for caminho, conteudo in ARQUIVOS.items():
        caminho_completo = os.path.join(PROJETO, caminho)
        diretorio = os.path.dirname(caminho_completo)
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(conteudo.lstrip('\n'))
        criado += 1
        print(f"  ✅ [{criado}/{total}] {caminho}")
    print()
    print("=" * 60)
    print(f"  🎉 PROJETO CRIADO COM SUCESSO!")
    print("=" * 60)
    print()
    print(f"  📁 Pasta: {os.path.abspath(PROJETO)}")
    print(f"  📊 Arquivos: {criado}")
    print()
    print("  🚀 PRÓXIMOS PASSOS:")
    print("  1. Commit e push no GitHub")
    print("  2. GitHub Actions compilará automaticamente")
    print("  3. Baixe o APK em Actions > Artifacts")
    print("=" * 60)


if __name__ == "__main__":
    try:
        criar_projeto()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
