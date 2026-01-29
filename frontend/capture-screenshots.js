/**
 * Script para capturar screenshots do Prova AI para o tutorial
 * Execute com: npx playwright install chromium && node capture-screenshots.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://ia-educacao-v2.onrender.com';
const OUTPUT_DIR = path.join(__dirname, 'tutorial-images');

// Garantir que a pasta existe
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function captureScreenshots() {
    console.log('🚀 Iniciando captura de screenshots...\n');
    
    const browser = await chromium.launch({ 
        headless: true,
        args: ['--no-sandbox']
    });
    
    const context = await browser.newContext({
        viewport: { width: 1400, height: 900 },
        deviceScaleFactor: 2, // Retina quality
    });
    
    const page = await context.newPage();
    
    try {
        // 1. Dashboard Principal
        console.log('📸 1/8 - Dashboard...');
        await page.goto(BASE_URL, { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        await page.screenshot({ 
            path: path.join(OUTPUT_DIR, '01-dashboard.png'),
            fullPage: false 
        });
        
        // 2. Sidebar expandido (hover na matéria se existir)
        console.log('📸 2/8 - Sidebar navegação...');
        // Tentar expandir uma matéria na sidebar
        const materiaItem = await page.$('.tree-item');
        if (materiaItem) {
            await materiaItem.click();
            await page.waitForTimeout(500);
        }
        await page.screenshot({ 
            path: path.join(OUTPUT_DIR, '02-sidebar.png'),
            clip: { x: 0, y: 0, width: 320, height: 900 }
        });
        
        // 3. Chat com IA
        console.log('📸 3/8 - Chat com IA...');
        await page.click('text=Chat com IA');
        await page.waitForTimeout(2000);
        await page.screenshot({ 
            path: path.join(OUTPUT_DIR, '03-chat.png'),
            fullPage: false 
        });
        
        // 4. Chat - Painel de filtros (se existir botão de filtro)
        console.log('📸 4/8 - Chat com filtros...');
        const filterBtn = await page.$('[data-mode="filtrar"]') || await page.$('text=Filtrar');
        if (filterBtn) {
            await filterBtn.click();
            await page.waitForTimeout(1000);
        }
        await page.screenshot({ 
            path: path.join(OUTPUT_DIR, '04-chat-filtros.png'),
            fullPage: false 
        });
        
        // 5. Modal de Configurações (API Keys)
        console.log('📸 5/8 - Configurações IA...');
        await page.click('text=Configurações IA');
        await page.waitForTimeout(1500);
        await page.screenshot({ 
            path: path.join(OUTPUT_DIR, '05-config-apikeys.png'),
            fullPage: false 
        });
        
        // 6. Aba de Modelos no modal de config
        console.log('📸 6/8 - Configuração de modelos...');
        const modelosTab = await page.$('text=Modelos') || await page.$('[data-tab="modelos"]');
        if (modelosTab) {
            await modelosTab.click();
            await page.waitForTimeout(1000);
        }
        await page.screenshot({ 
            path: path.join(OUTPUT_DIR, '06-config-modelos.png'),
            fullPage: false 
        });
        
        // Fechar modal
        const closeBtn = await page.$('.modal-close') || await page.$('button:has-text("×")');
        if (closeBtn) {
            await closeBtn.click();
            await page.waitForTimeout(500);
        }
        
        // 7. Modal Nova Matéria
        console.log('📸 7/8 - Nova Matéria...');
        await page.click('text=Nova Matéria');
        await page.waitForTimeout(1000);
        await page.screenshot({ 
            path: path.join(OUTPUT_DIR, '07-nova-materia.png'),
            fullPage: false 
        });
        
        // Fechar modal
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
        
        // 8. Navegar para uma atividade (se existir)
        console.log('📸 8/8 - Tela de atividade...');
        await page.click('text=Início');
        await page.waitForTimeout(1000);
        
        // Tentar clicar em uma matéria existente
        const materiaCard = await page.$('.materia-card') || await page.$('[onclick*="viewMateria"]');
        if (materiaCard) {
            await materiaCard.click();
            await page.waitForTimeout(1500);
            await page.screenshot({ 
                path: path.join(OUTPUT_DIR, '08-materia-view.png'),
                fullPage: false 
            });
        } else {
            // Screenshot do dashboard mesmo
            await page.screenshot({ 
                path: path.join(OUTPUT_DIR, '08-materia-view.png'),
                fullPage: false 
            });
        }
        
        console.log('\n✅ Screenshots capturados com sucesso!');
        console.log(`📁 Salvos em: ${OUTPUT_DIR}`);
        
    } catch (error) {
        console.error('❌ Erro durante captura:', error.message);
    } finally {
        await browser.close();
    }
}

captureScreenshots();
