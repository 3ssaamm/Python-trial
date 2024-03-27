using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
using System.Threading;

public class ThrusterControl : MonoBehaviour
{
    Thread mThread;
    public string connectionIP = "127.0.0.1"; // Default IP, changeable in Inspector
    public int connectionPort = 25001;        // Default port, changeable in Inspector
    TcpListener listener;
    TcpClient client;

    bool running;

    private void Start()
    {
        ThreadStart ts = new ThreadStart(InitSocket);
        mThread = new Thread(ts);
        mThread.Start();
    }

    void InitSocket()
    {
        listener = new TcpListener(IPAddress.Parse(connectionIP), connectionPort);
        listener.Start();
        client = listener.AcceptTcpClient();
        running = true;
        while (running)
        {
            ReceiveThrusterData();
        }
        listener.Stop();
    }


    void ReceiveThrusterData()
    {
        NetworkStream nwStream = client.GetStream();
        byte[] buffer = new byte[client.ReceiveBufferSize];
        int bytesRead = nwStream.Read(buffer, 0, client.ReceiveBufferSize);
        string dataReceived = Encoding.UTF8.GetString(buffer, 0, bytesRead);

        if (!string.IsNullOrEmpty(dataReceived) && dataReceived.StartsWith("fire_thrusters"))
        {
            // Parse the thruster data
            string[] thrusterData = dataReceived.Substring(15).Split(',');
            PrintThrusterData(thrusterData);
            
            // Send confirmation back to Python
            byte[] response = Encoding.ASCII.GetBytes("Thruster data received");
            nwStream.Write(response, 0, response.Length);
        }
    }

    void PrintThrusterData(string[] data)
    {
        for (int i = 0; i < data.Length; i++)
        {
            // Assuming the format is "magnitude,direction"
            string[] values = data[i].Split(',');
            if (values.Length == 2)
            {
                string magnitude = values[0];
                string direction = values[1];
                // Print to the console
                Debug.Log($"Thruster {i+1}: Magnitude: {magnitude}, Direction: {direction}");
            }
        }
    }

    private void OnApplicationQuit()
    {
        running = false;
    }
}
