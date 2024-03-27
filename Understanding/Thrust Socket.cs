using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
using System.Threading;

public class ThrusterControl : MonoBehaviour
{
    Thread mThread;
    public string connectionIP = "127.0.0.1";
    public int connectionPort = 25001;
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
            string thrusterData = dataReceived.Substring(15); // Remove the command part
            PrintThrusterData(thrusterData);
            
            // Send confirmation back to Python
            byte[] response = Encoding.ASCII.GetBytes("Thruster data received");
            nwStream.Write(response, 0, response.Length);
        }
    }

    void PrintThrusterData(string data)
    {
        // Split the data for each thruster
        string[] thrusters = data.Split(';');
        foreach (string thruster in thrusters)
        {
            // Split the name from the values
            string[] parts = thruster.Split(':');
            if (parts.Length == 2)
            {
                string thrusterName = parts[0];
                string values = parts[1];
                // Print to the console
                Debug.Log($"Thruster: {thrusterName}, Values: {values}");
            }
        }
    }

    private void OnApplicationQuit()
    {
        running = false;
    }
}
