import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Rebu Conductor'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.local_shipping, size: 80),
            const SizedBox(height: 20),
            const Text(
              'Rebu Conductor',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text('Ver FLUTTER_GUIDE.md para implementación completa'),
            const SizedBox(height: 40),
            ElevatedButton(
              onPressed: () {},
              child: const Text('Ver Ofertas'),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {},
              child: const Text('Mi Wallet'),
            ),
          ],
        ),
      ),
    );
  }
}
